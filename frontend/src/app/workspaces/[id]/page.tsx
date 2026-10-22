"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { api, downloadFile } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnCls, btnDanger, btnSecondary, cardCls, inputCls } from "@/components/ui";

interface Member { user_id: string; display_name: string | null; role: string }
interface Milestone { id: string; title: string; due_date: string | null; status: string }
interface Task { id: string; title: string; status: string; assignee_id: string | null; milestone_id: string | null }
interface Deliverable { id: string; title: string; has_file: boolean; status: string; submitted_at: string }
interface Feedback { id: string; author_name: string | null; body: string; rating: number | null; created_at: string }
interface Workspace {
  id: string; listing_id: string; listing_title: string | null;
  mentor_id: string | null; status: string;
  members: Member[]; milestones: Milestone[]; tasks: Task[];
  deliverables: Deliverable[]; feedback: Feedback[];
}
interface Mentor { user_id: string; display_name: string }

export default function WorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [ws, setWs] = useState<Workspace | null>(null);
  const [mentors, setMentors] = useState<Mentor[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [msTitle, setMsTitle] = useState("");
  const [taskTitle, setTaskTitle] = useState("");
  const [delivTitle, setDelivTitle] = useState("");
  const [fbBody, setFbBody] = useState("");
  const [fbRating, setFbRating] = useState("5");
  const [mentorSel, setMentorSel] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  async function load() {
    setWs(await api.get<Workspace>(`/workspaces/${id}`));
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) {
      load().catch(setError);
      api.get<Mentor[]>("/mentors").then(setMentors).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user, id]);

  if (loading || !user) return <Loading />;
  if (error) return <ErrorBox error={error} />;
  if (!ws) return <Loading />;

  const isMember = ws.members.some((m) => m.user_id === user.id);
  const isAdmin = user.role === "admin";
  const isMentor = ws.mentor_id === user.id;
  const canReview = isAdmin || isMentor || user.role === "provider";

  async function addMilestone(e: React.FormEvent) {
    e.preventDefault();
    await api.post(`/workspaces/${id}/milestones`, { title: msTitle });
    setMsTitle("");
    await load();
  }

  async function addTask(e: React.FormEvent) {
    e.preventDefault();
    await api.post(`/workspaces/${id}/tasks`, { title: taskTitle });
    setTaskTitle("");
    await load();
  }

  async function setTaskStatus(t: Task, status: string) {
    await api.patch(`/tasks/${t.id}`, { status });
    await load();
  }

  async function assignTask(t: Task, assignee: string) {
    await api.patch(`/tasks/${t.id}`, { assignee_id: assignee || null });
    await load();
  }

  async function submitDeliverable(e: React.FormEvent) {
    e.preventDefault();
    const fd = new FormData();
    fd.set("title", delivTitle);
    const f = fileRef.current?.files?.[0];
    if (f) fd.set("file", f);
    await api.upload(`/workspaces/${id}/deliverables`, fd);
    setDelivTitle("");
    if (fileRef.current) fileRef.current.value = "";
    await load();
  }

  async function review(delivId: string, action: "approve" | "request-changes") {
    await api.post(`/deliverables/${delivId}/${action}`);
    await load();
  }

  async function addFeedback(e: React.FormEvent) {
    e.preventDefault();
    await api.post(`/workspaces/${id}/feedback`, {
      body: fbBody, rating: Number(fbRating),
    });
    setFbBody("");
    await load();
  }

  async function submitWs() {
    await api.post(`/workspaces/${id}/submit`);
    await load();
  }

  async function completeWs() {
    try {
      await api.post(`/workspaces/${id}/complete`);
      await load();
    } catch (e) {
      setError(e);
    }
  }

  async function assignMentor() {
    if (!mentorSel) return;
    try {
      await api.post(`/workspaces/${id}/assign-mentor`, { mentor_id: mentorSel });
      await load();
    } catch (e) {
      setError(e);
    }
  }

  return (
    <div className="space-y-4">
      <div className={cardCls}>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{ws.listing_title}</h1>
            <p className="mt-1 text-sm text-gray-500">
              {ws.members.map((m) => m.display_name).join(", ")}
            </p>
          </div>
          <Badge color={ws.status === "completed" ? "green" : ws.status === "submitted" ? "yellow" : "blue"}>
            {ws.status}
          </Badge>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
          {ws.status === "active" && isMember && (
            <button onClick={submitWs} className={btnSecondary}>Submit for completion</button>
          )}
          {isAdmin && ws.status !== "completed" && (
            <button onClick={completeWs} className={btnCls}>Mark completed</button>
          )}
          {!ws.mentor_id && canReview && mentors.length > 0 && (
            <span className="flex items-center gap-2">
              <select className={inputCls} value={mentorSel}
                onChange={(e) => setMentorSel(e.target.value)} style={{ width: "auto" }}>
                <option value="">Assign mentor…</option>
                {mentors.map((m) => (
                  <option key={m.user_id} value={m.user_id}>{m.display_name}</option>
                ))}
              </select>
              <button onClick={assignMentor} className={btnSecondary}>Assign</button>
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className={cardCls}>
          <h2 className="font-semibold">Milestones</h2>
          <form onSubmit={addMilestone} className="mt-2 flex gap-2">
            <input className={inputCls} placeholder="New milestone" required
              value={msTitle} onChange={(e) => setMsTitle(e.target.value)} />
            <button className={btnCls}>Add</button>
          </form>
          <ul className="mt-3 space-y-2">
            {ws.milestones.length === 0 && <Empty>No milestones yet.</Empty>}
            {ws.milestones.map((m) => (
              <li key={m.id} className="flex items-center justify-between text-sm">
                <span>{m.title}</span>
                <Badge color={m.status === "done" ? "green" : "gray"}>{m.status}</Badge>
              </li>
            ))}
          </ul>
        </div>

        <div className={cardCls}>
          <h2 className="font-semibold">Tasks</h2>
          <form onSubmit={addTask} className="mt-2 flex gap-2">
            <input className={inputCls} placeholder="New task" required
              value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} />
            <button className={btnCls}>Add</button>
          </form>
          <ul className="mt-3 space-y-2">
            {ws.tasks.length === 0 && <Empty>No tasks yet.</Empty>}
            {ws.tasks.map((t) => (
              <li key={t.id} className="flex items-center justify-between gap-2 text-sm">
                <span className={t.status === "done" ? "line-through text-gray-400" : ""}>
                  {t.title}
                </span>
                <span className="flex items-center gap-2">
                  <select value={t.assignee_id ?? ""} onChange={(e) => assignTask(t, e.target.value)}
                    className="rounded border border-gray-300 px-1 py-0.5 text-xs">
                    <option value="">unassigned</option>
                    {ws.members.map((m) => (
                      <option key={m.user_id} value={m.user_id}>{m.display_name}</option>
                    ))}
                  </select>
                  <select value={t.status} onChange={(e) => setTaskStatus(t, e.target.value)}
                    className="rounded border border-gray-300 px-1 py-0.5 text-xs">
                    <option value="todo">todo</option>
                    <option value="in_progress">in progress</option>
                    <option value="done">done</option>
                  </select>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className={cardCls}>
        <h2 className="font-semibold">Deliverables</h2>
        {ws.status !== "completed" && (
          <form onSubmit={submitDeliverable} className="mt-2 flex flex-wrap items-center gap-2">
            <input className={`${inputCls} max-w-xs`} placeholder="Deliverable title" required
              value={delivTitle} onChange={(e) => setDelivTitle(e.target.value)} />
            <input ref={fileRef} type="file" className="text-sm" />
            <button className={btnCls}>Submit</button>
          </form>
        )}
        <ul className="mt-3 space-y-2">
          {ws.deliverables.length === 0 && <Empty>No deliverables submitted yet.</Empty>}
          {ws.deliverables.map((d) => (
            <li key={d.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-gray-200 p-3 text-sm">
              <div>
                <span className="font-medium">{d.title}</span>
                <span className="ml-2 text-xs text-gray-500">
                  {new Date(d.submitted_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Badge color={d.status === "approved" ? "green" : d.status === "changes_requested" ? "red" : "gray"}>
                  {d.status.replace("_", " ")}
                </Badge>
                {d.has_file && (
                  <button onClick={() => downloadFile(`/deliverables/${d.id}/download`, d.title)}
                    className="text-blue-600 text-xs underline">download</button>
                )}
                {canReview && d.status === "submitted" && (
                  <>
                    <button onClick={() => review(d.id, "approve")} className={btnCls}>Approve</button>
                    <button onClick={() => review(d.id, "request-changes")} className={btnDanger}>
                      Request changes
                    </button>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className={cardCls}>
        <h2 className="font-semibold">Feedback</h2>
        {canReview && (
          <form onSubmit={addFeedback} className="mt-2 flex flex-wrap items-center gap-2">
            <input className={`${inputCls} flex-1`} placeholder="Write feedback…" required
              value={fbBody} onChange={(e) => setFbBody(e.target.value)} />
            <select className={inputCls} style={{ width: "auto" }} value={fbRating}
              onChange={(e) => setFbRating(e.target.value)}>
              {[5, 4, 3, 2, 1].map((r) => <option key={r} value={r}>{r}★</option>)}
            </select>
            <button className={btnCls}>Send</button>
          </form>
        )}
        <ul className="mt-3 space-y-2">
          {ws.feedback.length === 0 && <Empty>No feedback yet.</Empty>}
          {ws.feedback.map((f) => (
            <li key={f.id} className="rounded-md border border-gray-200 p-3 text-sm">
              <div className="flex justify-between text-xs text-gray-500">
                <span className="font-medium text-gray-700">{f.author_name ?? "Reviewer"}</span>
                <span>{f.rating ? `${f.rating}★ · ` : ""}{new Date(f.created_at).toLocaleDateString()}</span>
              </div>
              <p className="mt-1">{f.body}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
