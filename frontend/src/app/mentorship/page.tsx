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

interface Slot {
  id: string;
  starts_at: string;
  ends_at: string;
  booking_id: string | null;
  booking_status: string | null;
}

interface Booking {
  id: string;
  slot_id: string;
  mentor_id: string;
  student_id: string;
  student_name: string | null;
  mentor_name: string | null;
  topic: string | null;
  note: string | null;
  status: string;
  meeting_link: string | null;
  starts_at: string;
  ends_at: string;
}

export default function MentorshipPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Req[] | null>(null);
  const [sessions, setSessions] = useState<Record<string, Session[]>>({});
  const [error, setError] = useState<unknown>(null);
  const [sched, setSched] = useState<Record<string, string>>({});
  const [slots, setSlots] = useState<Slot[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [slotForm, setSlotForm] = useState({ starts: "", ends: "" });

  async function load() {
    const [reqs, bks] = await Promise.all([
      api.get<Req[]>("/mentor-requests/mine"),
      api.get<Booking[]>("/mentor-bookings/mine"),
    ]);
    setItems(reqs);
    setBookings(bks);
    if (user?.role === "mentor") {
      setSlots(await api.get<Slot[]>("/me/mentor-slots").catch(() => []));
    }
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

  async function addSlot() {
    if (!slotForm.starts || !slotForm.ends) return;
    try {
      await api.post("/me/mentor-slots", {
        slots: [{
          starts_at: new Date(slotForm.starts).toISOString(),
          ends_at: new Date(slotForm.ends).toISOString(),
        }],
      });
      setSlotForm({ starts: "", ends: "" });
      await load();
    } catch (e) { setError(e); }
  }

  async function removeSlot(id: string) {
    try {
      await api.del(`/me/mentor-slots/${id}`);
      await load();
    } catch (e) { setError(e); }
  }

  async function bookingAction(id: string, action: string) {
    try {
      await api.post(`/mentor-bookings/${id}/${action}`);
      await load();
    } catch (e) { setError(e); }
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

      {user.role === "mentor" && (
        <div className={cardCls}>
          <h2 className="font-semibold">My availability</h2>
          <p className="mt-1 text-xs text-gray-500">
            Students can book open slots from your mentor profile.
          </p>
          <div className="mt-3 flex flex-wrap items-end gap-2">
            <label className="text-sm text-gray-700">
              Start
              <input type="datetime-local" className={`${inputCls} mt-1`} value={slotForm.starts}
                onChange={(e) => setSlotForm({ ...slotForm, starts: e.target.value })} />
            </label>
            <label className="text-sm text-gray-700">
              End
              <input type="datetime-local" className={`${inputCls} mt-1`} value={slotForm.ends}
                onChange={(e) => setSlotForm({ ...slotForm, ends: e.target.value })} />
            </label>
            <button onClick={addSlot} className={btnCls}>Add slot</button>
          </div>
          {slots.length > 0 && (
            <ul className="mt-4 space-y-2">
              {slots.map((s) => (
                <li key={s.id}
                  className="flex items-center justify-between rounded-md border border-gray-200 p-2.5">
                  <span className="text-sm">
                    {new Date(s.starts_at).toLocaleString()} —{" "}
                    {new Date(s.ends_at).toLocaleTimeString()}
                  </span>
                  <span className="flex items-center gap-2">
                    {s.booking_status ? (
                      <Badge color={s.booking_status === "confirmed" ? "green" : "yellow"}>
                        {s.booking_status}
                      </Badge>
                    ) : (
                      <>
                        <Badge color="blue">open</Badge>
                        <button onClick={() => removeSlot(s.id)} className={btnDanger}>Delete</button>
                      </>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {bookings.length > 0 && (
        <div className={cardCls}>
          <h2 className="font-semibold">Session bookings</h2>
          <ul className="mt-3 space-y-3">
            {bookings.map((b) => {
              const isMentor = b.mentor_id === user.id;
              const isStudent = b.student_id === user.id;
              const ended = new Date(b.ends_at) < new Date();
              return (
                <li key={b.id} className="rounded-md border border-gray-200 p-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">
                      {isMentor ? b.student_name : b.mentor_name}
                      {b.topic ? ` — ${b.topic}` : ""}
                    </span>
                    <Badge color={
                      b.status === "confirmed" ? "green" :
                      b.status === "completed" ? "blue" :
                      b.status === "pending" ? "yellow" : "gray"
                    }>{b.status.replace("_", " ")}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-gray-600">
                    {new Date(b.starts_at).toLocaleString()} —{" "}
                    {new Date(b.ends_at).toLocaleTimeString()}
                  </p>
                  {b.note && <p className="mt-1 text-sm text-gray-600">{b.note}</p>}
                  {b.meeting_link && b.status === "confirmed" && (
                    <a className="mt-1 block text-sm text-accent underline"
                      href={b.meeting_link} target="_blank" rel="noreferrer">
                      Join meeting
                    </a>
                  )}
                  <div className="mt-2 flex flex-wrap gap-2">
                    {isMentor && b.status === "pending" && (
                      <>
                        <button onClick={() => bookingAction(b.id, "confirm")} className={btnCls}>Confirm</button>
                        <button onClick={() => bookingAction(b.id, "decline")} className={btnDanger}>Decline</button>
                      </>
                    )}
                    {(b.status === "pending" || b.status === "confirmed") && (isMentor || isStudent) && (
                      <button onClick={() => bookingAction(b.id, "cancel")} className={btnSecondary}>Cancel</button>
                    )}
                    {isMentor && b.status === "confirmed" && ended && (
                      <>
                        <button onClick={() => bookingAction(b.id, "complete")} className={btnCls}>Mark completed</button>
                        <button onClick={() => bookingAction(b.id, "no-show")} className={btnSecondary}>No-show</button>
                      </>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
