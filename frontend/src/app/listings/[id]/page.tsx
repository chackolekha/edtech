"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, ErrorBox, Loading, btnCls, btnDanger, btnSecondary, cardCls, inputCls } from "@/components/ui";
import type { Listing } from "../page";

interface Application {
  id: string;
  student_id: string;
  student_name: string | null;
  cover_note: string | null;
  status: string;
}

interface Mentor {
  user_id: string;
  display_name: string;
}

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [listing, setListing] = useState<Listing | null>(null);
  const [apps, setApps] = useState<Application[]>([]);
  const [mentors, setMentors] = useState<Mentor[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [note, setNote] = useState("");
  const [teamName, setTeamName] = useState("Team 1");
  const [mentorId, setMentorId] = useState("");
  const [teamId, setTeamId] = useState<string | null>(null);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);

  const isAuthor = user && listing && listing.author_id === user.id;
  const isAdmin = user?.role === "admin";
  const canReview = isAuthor || isAdmin;

  async function load() {
    const l = await api.get<Listing>(`/listings/${id}`);
    setListing(l);
    try {
      setApps(await api.get<Application[]>(`/listings/${id}/applications`));
    } catch {
      setApps([]);
    }
    try {
      const t = await api.get<{ id: string; workspace_id: string }>(`/listings/${id}/team`);
      setTeamId(t.id);
      setWorkspaceId(t.workspace_id);
    } catch {
      setTeamId(null);
    }
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
  if (!listing) return <Loading />;

  async function apply() {
    await api.post(`/listings/${id}/apply`, { cover_note: note || null });
    await load();
  }

  async function setAppStatus(appId: string, action: "accept" | "reject") {
    await api.post(`/applications/${appId}/${action}`);
    await load();
  }

  async function publish() {
    await api.post(`/listings/${id}/publish`);
    await load();
  }

  async function closeListing() {
    await api.post(`/listings/${id}/close`);
    await load();
  }

  async function formTeam() {
    const accepted = apps.filter((a) => a.status === "accepted").map((a) => a.id);
    if (accepted.length === 0) {
      setError(new Error("Accept at least one application first"));
      return;
    }
    try {
      const team = await api.post<{ workspace_id: string }>(
        `/listings/${id}/form-team`,
        { name: teamName, application_ids: accepted, mentor_id: mentorId || null },
      );
      setWorkspaceId(team.workspace_id);
      await load();
    } catch (e) {
      setError(e);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className={cardCls}>
        <div className="flex items-start justify-between gap-3">
          <h1 className="text-2xl font-bold">{listing.title}</h1>
          <Badge color={listing.status === "open" ? "green" : "gray"}>{listing.status}</Badge>
        </div>
        <p className="mt-1 text-sm text-gray-500">
          by {listing.author_name} · team of {listing.team_size}
          {listing.duration_weeks ? ` · ${listing.duration_weeks} weeks` : ""}
          {listing.category ? ` · ${listing.category}` : ""}
        </p>
        <p className="mt-3 whitespace-pre-wrap text-gray-800">{listing.brief}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {listing.required_skills.map((s) => <Badge key={s}>{s}</Badge>)}
        </div>
        {canReview && listing.status === "draft" && (
          <button onClick={publish} className={`${btnCls} mt-4`}>Publish listing</button>
        )}
        {canReview && listing.status === "open" && (
          <button onClick={closeListing} className={`${btnSecondary} mt-4`}>Close listing</button>
        )}
        {workspaceId && (
          <p className="mt-4 text-sm">
            Team formed —{" "}
            <Link href={`/workspaces/${workspaceId}`} className="text-blue-600 underline">
              open workspace →
            </Link>
          </p>
        )}
      </div>

      {user.role === "student" && listing.status === "open" && !listing.my_application_id && (
        <div className={cardCls}>
          <h2 className="font-semibold">Apply</h2>
          <textarea className={`${inputCls} mt-2`} rows={3}
            placeholder="Cover note — why are you a good fit?"
            value={note} onChange={(e) => setNote(e.target.value)} />
          <button onClick={apply} className={`${btnCls} mt-2`}>Submit application</button>
        </div>
      )}
      {listing.my_application_id && (
        <p className="text-sm text-green-700">You applied to this project. Track it under <Link href="/applications" className="underline">Applications</Link>.</p>
      )}

      {canReview && (
        <div className={cardCls}>
          <h2 className="font-semibold">Applications ({apps.length})</h2>
          {apps.length === 0 ? (
            <p className="mt-2 text-sm text-gray-500">No applications yet.</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {apps.map((a) => (
                <li key={a.id} className="rounded-md border border-gray-200 p-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{a.student_name ?? "Student"}</span>
                    <Badge color={a.status === "accepted" ? "green" : a.status === "rejected" ? "red" : "gray"}>
                      {a.status}
                    </Badge>
                  </div>
                  {a.cover_note && <p className="mt-1 text-sm text-gray-600">{a.cover_note}</p>}
                  {a.status === "submitted" && (
                    <div className="mt-2 flex gap-2">
                      <button onClick={() => setAppStatus(a.id, "accept")} className={btnCls}>
                        Accept
                      </button>
                      <button onClick={() => setAppStatus(a.id, "reject")} className={btnDanger}>
                        Reject
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
          {!teamId && apps.some((a) => a.status === "accepted") && (
            <div className="mt-4 border-t border-gray-200 pt-4">
              <h3 className="font-medium">Form team & create workspace</h3>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <input className={`${inputCls} max-w-xs`} value={teamName}
                  onChange={(e) => setTeamName(e.target.value)} placeholder="Team name" />
                <select className={`${inputCls} max-w-xs`} value={mentorId}
                  onChange={(e) => setMentorId(e.target.value)}>
                  <option value="">No mentor</option>
                  {mentors.map((m) => (
                    <option key={m.user_id} value={m.user_id}>{m.display_name}</option>
                  ))}
                </select>
                <button onClick={formTeam} className={btnCls}>Form team</button>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                All accepted applicants join the team; a private workspace is created.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
