from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db

# Import all models so Base.metadata is complete for Alembic autogenerate.
from app.modules.admin.models import AuditEvent, ModerationFlag  # noqa: F401
from app.modules.auth.models import AuthToken, User  # noqa: F401
from app.modules.communities.models import (  # noqa: F401
    Comment, Community, CommunityMember, Post, Reaction,
)
from app.modules.mentoring.models import MentorRequest, MentorSession  # noqa: F401
from app.modules.portfolio.models import PortfolioItem  # noqa: F401
from app.modules.profiles.models import (  # noqa: F401
    Interest, MentorProfile, Profile, Skill, UserInterest, UserSkill,
)
from app.modules.projects.models import Application, Listing, Team, TeamMember  # noqa: F401
from app.modules.trainings.models import (  # noqa: F401
    Enrollment, Lesson, LessonProgress, Training,
)
from app.modules.workspaces.models import (  # noqa: F401
    Deliverable, Feedback, Milestone, Task, Workspace,
)

from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.communities.router import router as communities_router
from app.modules.mentoring.router import router as mentoring_router
from app.modules.notifications.router import router as notifications_router
from app.modules.portfolio.router import router as portfolio_router
from app.modules.profiles.router import router as profiles_router
from app.modules.projects.router import router as projects_router
from app.modules.trainings.router import router as trainings_router
from app.modules.workspaces.router import router as workspaces_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="EdTech Platform API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health(db: Session = Depends(get_db)):
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}

    for r in (
        auth_router, profiles_router, communities_router, mentoring_router,
        projects_router, workspaces_router, trainings_router, portfolio_router,
        notifications_router, admin_router,
    ):
        app.include_router(r, prefix="/api/v1")
    return app


app = create_app()
