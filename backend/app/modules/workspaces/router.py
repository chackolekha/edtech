import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.enums import (
    DeliverableStatus,
    Role,
    VerificationStatus,
    WorkspaceStatus,
)
from app.modules.auth.models import User
from app.modules.notifications.service import notify
from app.modules.profiles.models import Profile
from app.modules.projects.models import Listing, TeamMember
from app.modules.workspaces import schemas, service
from app.modules.workspaces.models import Deliverable, Feedback, Milestone, Task, Workspace

router = APIRouter(tags=["workspaces"])


@router.get("/workspaces/mine")
def my_workspaces(user=Depends(get_current_user), db: Session = Depends(get_db)):
    query = select(Workspace)
    if user.role == Role.student:
        query = query.join(TeamMember, TeamMember.team_id == Workspace.team_id).where(
            TeamMember.user_id == user.id
        )
    elif user.role == Role.mentor:
        query = query.where(Workspace.mentor_id == user.id)
    elif user.role == Role.provider:
        query = query.join(Listing, Listing.id == Workspace.listing_id).where(
            Listing.author_id == user.id
        )
    rows = db.scalars(query.order_by(Workspace.created_at.desc())).all()
    return [
        {"id": w.id, "listing_id": w.listing_id, "status": w.status,
         "listing_title": (l.title if (l := db.get(Listing, w.listing_id)) else None)}
        for w in rows
    ]


@router.get("/workspaces/{workspace_id}", response_model=schemas.WorkspaceOut)
def get_workspace(workspace_id: uuid.UUID, user=Depends(get_current_user),
                  db: Session = Depends(get_db)):
    ws = service.get_workspace_or_404(db, workspace_id)
    service.require_view(db, ws, user)
    return service.workspace_detail(db, ws)


@router.post("/workspaces/{workspace_id}/assign-mentor", response_model=schemas.WorkspaceOut)
def assign_mentor(workspace_id: uuid.UUID, body: schemas.AssignMentorIn,
                  user=Depends(get_current_user), db: Session = Depends(get_db)):
    ws = service.get_workspace_or_404(db, workspace_id)
    listing = db.get(Listing, ws.listing_id)
    if listing.author_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Only the project owner or admin can assign a mentor")
    mentor = db.get(User, body.mentor_id)
    if mentor is None or mentor.role != Role.mentor or \
            mentor.verification_status != VerificationStatus.verified:
        raise HTTPException(422, "Mentor must be a verified mentor")
    ws.mentor_id = body.mentor_id
    db.commit()
    return service.workspace_detail(db, ws)


@router.post("/workspaces/{workspace_id}/milestones", response_model=schemas.MilestoneOut, status_code=201)
def add_milestone(workspace_id: uuid.UUID, body: schemas.MilestoneIn,
                  user=Depends(get_current_user), db: Session = Depends(get_db)):
    ws = service.get_workspace_or_404(db, workspace_id)
    service.require_edit(db, ws, user)
    m = Milestone(workspace_id=ws.id, title=body.title, due_date=body.due_date,
                  position=body.position)
    db.add(m)
    db.commit()
    return m


@router.patch("/milestones/{milestone_id}", response_model=schemas.MilestoneOut)
def update_milestone(milestone_id: uuid.UUID, body: schemas.MilestonePatch,
                     user=Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.get(Milestone, milestone_id)
    if m is None:
        raise HTTPException(404, "Milestone not found")
    ws = service.get_workspace_or_404(db, m.workspace_id)
    service.require_edit(db, ws, user)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(m, k, v)
    db.commit()
    return m


@router.post("/workspaces/{workspace_id}/tasks", response_model=schemas.TaskOut, status_code=201)
def add_task(workspace_id: uuid.UUID, body: schemas.TaskIn,
             user=Depends(get_current_user), db: Session = Depends(get_db)):
    ws = service.get_workspace_or_404(db, workspace_id)
    service.require_edit(db, ws, user)
    if body.assignee_id and not db.get(TeamMember, (ws.team_id, body.assignee_id)):
        raise HTTPException(422, "Assignee must be a team member")
    t = Task(workspace_id=ws.id, title=body.title, description=body.description,
             assignee_id=body.assignee_id, milestone_id=body.milestone_id)
    db.add(t)
    db.commit()
    return t


@router.patch("/tasks/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: uuid.UUID, body: schemas.TaskPatch,
                user=Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.get(Task, task_id)
    if t is None:
        raise HTTPException(404, "Task not found")
    ws = service.get_workspace_or_404(db, t.workspace_id)
    service.require_edit(db, ws, user)
    data = body.model_dump(exclude_unset=True)
    if data.get("assignee_id") and not db.get(TeamMember, (ws.team_id, data["assignee_id"])):
        raise HTTPException(422, "Assignee must be a team member")
    for k, v in data.items():
        setattr(t, k, v)
    db.commit()
    return t


@router.post("/workspaces/{workspace_id}/deliverables",
             response_model=schemas.DeliverableOut, status_code=201)
def submit_deliverable(
    workspace_id: uuid.UUID,
    title: str = Form(min_length=1, max_length=200),
    milestone_id: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = service.get_workspace_or_404(db, workspace_id)
    service.require_edit(db, ws, user)
    file_key = service.store_file(file) if file and file.filename else None
    d = Deliverable(
        workspace_id=ws.id, title=title, file_key=file_key, submitted_by=user.id,
        milestone_id=uuid.UUID(milestone_id) if milestone_id else None,
    )
    db.add(d)
    db.commit()
    return {"id": d.id, "workspace_id": d.workspace_id, "milestone_id": d.milestone_id,
            "title": d.title, "has_file": d.file_key is not None,
            "submitted_by": d.submitted_by, "submitted_at": d.submitted_at, "status": d.status}


def _get_deliverable_and_check(db: Session, deliverable_id: uuid.UUID, user, review: bool):
    d = db.get(Deliverable, deliverable_id)
    if d is None:
        raise HTTPException(404, "Deliverable not found")
    ws = service.get_workspace_or_404(db, d.workspace_id)
    if review:
        service.require_review(db, ws, user)
    else:
        service.require_view(db, ws, user)
    return d, ws


@router.get("/deliverables/{deliverable_id}/download")
def download_deliverable(deliverable_id: uuid.UUID, user=Depends(get_current_user),
                         db: Session = Depends(get_db)):
    d, _ = _get_deliverable_and_check(db, deliverable_id, user, review=False)
    if not d.file_key:
        raise HTTPException(404, "No file attached")
    path = service.file_path(d.file_key)
    return FileResponse(path, filename=d.file_key.split("_", 1)[-1])


@router.post("/deliverables/{deliverable_id}/approve", response_model=schemas.DeliverableOut)
def approve_deliverable(deliverable_id: uuid.UUID, user=Depends(get_current_user),
                        db: Session = Depends(get_db)):
    d, ws = _get_deliverable_and_check(db, deliverable_id, user, review=True)
    d.status = DeliverableStatus.approved
    db.commit()
    return {"id": d.id, "workspace_id": d.workspace_id, "milestone_id": d.milestone_id,
            "title": d.title, "has_file": d.file_key is not None,
            "submitted_by": d.submitted_by, "submitted_at": d.submitted_at, "status": d.status}


@router.post("/deliverables/{deliverable_id}/request-changes", response_model=schemas.DeliverableOut)
def request_changes(deliverable_id: uuid.UUID, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    d, ws = _get_deliverable_and_check(db, deliverable_id, user, review=True)
    d.status = DeliverableStatus.changes_requested
    db.commit()
    return {"id": d.id, "workspace_id": d.workspace_id, "milestone_id": d.milestone_id,
            "title": d.title, "has_file": d.file_key is not None,
            "submitted_by": d.submitted_by, "submitted_at": d.submitted_at, "status": d.status}


@router.post("/workspaces/{workspace_id}/feedback", response_model=schemas.FeedbackOut, status_code=201)
def add_feedback(workspace_id: uuid.UUID, body: schemas.FeedbackIn,
                 user=Depends(get_current_user), db: Session = Depends(get_db)):
    ws = service.get_workspace_or_404(db, workspace_id)
    service.require_review(db, ws, user)
    if body.deliverable_id:
        d = db.get(Deliverable, body.deliverable_id)
        if d is None or d.workspace_id != ws.id:
            raise HTTPException(422, "Deliverable not in this workspace")
    f = Feedback(workspace_id=ws.id, author_id=user.id, body=body.body,
                 rating=body.rating, deliverable_id=body.deliverable_id)
    db.add(f)
    for (uid,) in db.execute(
        select(TeamMember.user_id).where(TeamMember.team_id == ws.team_id)
    ):
        notify(db, uid, "feedback_received", {"workspace_id": str(ws.id)})
    db.commit()
    p = db.get(Profile, user.id)
    return {"id": f.id, "workspace_id": f.workspace_id, "author_id": f.author_id,
            "author_name": p.display_name if p else None, "deliverable_id": f.deliverable_id,
            "body": f.body, "rating": f.rating, "created_at": f.created_at}


@router.post("/workspaces/{workspace_id}/submit", response_model=schemas.WorkspaceOut)
def submit_workspace(workspace_id: uuid.UUID, user=Depends(get_current_user),
                     db: Session = Depends(get_db)):
    ws = service.get_workspace_or_404(db, workspace_id)
    service.require_edit(db, ws, user)
    if ws.status != WorkspaceStatus.active:
        raise HTTPException(409, "Workspace is not active")
    ws.status = WorkspaceStatus.submitted
    db.commit()
    return service.workspace_detail(db, ws)


@router.post("/workspaces/{workspace_id}/complete", response_model=schemas.WorkspaceOut)
def complete_workspace(workspace_id: uuid.UUID, user=Depends(get_current_user),
                       db: Session = Depends(get_db)):
    if user.role != Role.admin:
        raise HTTPException(403, "Only admins can mark a workspace completed")
    ws = service.get_workspace_or_404(db, workspace_id)
    service.complete_workspace(db, ws, user)
    return service.workspace_detail(db, ws)
