"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnCls, btnDanger, btnSecondary, cardCls, inputCls } from "@/components/ui";

interface Req {
  id: string;
  student_id: string;
  mentor_id: string;
  student_name: string | null;
  mentor_name: string | null;
  message: string | null;
  status: string;
}

interface Session {
  id: string;
  scheduled_at: string;
  notes: string | null;
}

export default function MentorshipPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Req[] | null>(null);
  const [sessions, setSessions] = useState<Record<string, Session[]>>({});
  const [error, setError] = useState<unknown>(null);
  const [sched, setSched] = useState<Record<string, string>>({});

  async function load() {
    setItems(await api.get<Req[]>("/mentor-requests/mine"));
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load().catch(setError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  if (loading || !user) return <Loading />;

  async function respond(id: string, action: "accept" | "decline") {
    await api.post(`/mentor-requests/${id}/${action}`);
    await load();
  }

  async function end(id: string) {
    await api.post(`/mentor-requests/${id}/end`);
    await load();
  }

  async function toggleSessions(id: string) {
    if (sessions[id]) {
      setSessions((s) => ({ ...s, [id]: undefined as unknown as Session[] }));
      return;
    }
    const s = await api.get<Session[]>(`/mentor-requests/${id}/sessions`);
    setSessions((prev) => ({ ...prev, [id]: s }));
  }

  async function addSession(id: string) {
    if (!sched[id]) return;
    await api.post(`/mentor-requests/${id}/sessions`, {
      scheduled_at: new Date(sched[id]).toISOString(),
    });
    const s = await api.get<Session[]>(`/mentor-requests/${id}/sessions`);
    setSessions((prev) => ({ ...prev, [id]: s }));
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-bold">Mentorship</h1>
      <ErrorBox error={error} />
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty>No mentorship requests yet.</Empty>
      ) : (
        items.map((r) => {
          const isMentor = r.mentor_id === user.id;
          return (
            <div key={r.id} className={cardCls}>
              <div className="flex items-center justify-between">
                <span className="font-medium">
                  {isMentor ? `From ${r.student_name}` : `To ${r.mentor_name}`}
                </span>
                <Badge color={
                  r.status === "accepted" ? "green" :
                  r.status === "declined" ? "red" :
                  r.status === "ended" ? "gray" : "yellow"
                }>{r.status}</Badge>
              </div>
              {r.message && <p className="mt-1 text-sm text-gray-600">{r.message}</p>}
              <div className="mt-3 flex flex-wrap gap-2">
                {isMentor && r.status === "pending" && (
                  <>
                    <button onClick={() => respond(r.id, "accept")} className={btnCls}>Accept</button>
                    <button onClick={() => respond(r.id, "decline")} className={btnDanger}>Decline</button>
                  </>
                )}
                {r.status === "accepted" && (
                  <>
                    <button onClick={() => toggleSessions(r.id)} className={btnSecondary}>
                      Sessions
                    </button>
                    <button onClick={() => end(r.id)} className={btnDanger}>End mentorship</button>
                  </>
                )}
              </div>
              {r.status === "accepted" && sessions[r.id] !== undefined && (
                <div className="mt-3 border-t border-gray-200 pt-3">
                  <ul className="space-y-1 text-sm">
                    {(sessions[r.id] ?? []).map((s) => (
                      <li key={s.id}>
                        {new Date(s.scheduled_at).toLocaleString()}
                        {s.notes ? ` — ${s.notes}` : ""}
                      </li>
                    ))}
                    {(sessions[r.id] ?? []).length === 0 && (
                      <li className="text-gray-500">No sessions scheduled.</li>
                    )}
                  </ul>
                  <div className="mt-2 flex gap-2">
                    <input type="datetime-local" className={inputCls}
                      value={sched[r.id] ?? ""}
                      onChange={(e) => setSched({ ...sched, [r.id]: e.target.value })} />
                    <button onClick={() => addSession(r.id)} className={btnSecondary}>
                      Schedule
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })
      )}
    </div>
  );
}
