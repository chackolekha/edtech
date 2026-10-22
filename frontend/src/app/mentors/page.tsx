"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnCls, cardCls, inputCls } from "@/components/ui";

interface Mentor {
  user_id: string;
  display_name: string;
  headline: string | null;
  expertise: string | null;
  availability: string | null;
  accepting_requests: boolean;
  skills: string[];
}

export default function MentorsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Mentor[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [q, setQ] = useState("");
  const [msg, setMsg] = useState<Record<string, string>>({});
  const [sent, setSent] = useState<Record<string, boolean>>({});

  async function load(query = "") {
    setItems(await api.get<Mentor[]>(`/mentors${query ? `?q=${encodeURIComponent(query)}` : ""}`));
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load().catch(setError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  if (loading || !user) return <Loading />;

  async function request(mentorId: string) {
    try {
      await api.post("/mentor-requests", {
        mentor_id: mentorId, message: msg[mentorId] || null,
      });
      setSent((s) => ({ ...s, [mentorId]: true }));
    } catch (e) {
      setError(e);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Find a mentor</h1>
        <form onSubmit={(e) => { e.preventDefault(); load(q).catch(setError); }} className="flex gap-2">
          <input className={inputCls} placeholder="Search…" value={q}
            onChange={(e) => setQ(e.target.value)} />
          <button className={btnCls}>Search</button>
        </form>
      </div>
      <ErrorBox error={error} />
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty>No verified mentors yet.</Empty>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((m) => (
            <div key={m.user_id} className={cardCls}>
              <h2 className="font-semibold">{m.display_name}</h2>
              {m.headline && <p className="text-sm text-gray-600">{m.headline}</p>}
              {m.expertise && <p className="mt-1 text-sm text-gray-700">{m.expertise}</p>}
              <div className="mt-2 flex flex-wrap gap-1.5">
                {m.skills.map((s) => <Badge key={s}>{s}</Badge>)}
              </div>
              <p className="mt-1 text-xs text-gray-500">{m.availability}</p>
              {user.role === "student" && m.accepting_requests && !sent[m.user_id] && (
                <div className="mt-3 flex gap-2">
                  <input className={inputCls} placeholder="Message (optional)"
                    value={msg[m.user_id] ?? ""}
                    onChange={(e) => setMsg({ ...msg, [m.user_id]: e.target.value })} />
                  <button onClick={() => request(m.user_id)} className={btnCls}>Request</button>
                </div>
              )}
              {sent[m.user_id] && <Badge color="green">request sent</Badge>}
              {!m.accepting_requests && <Badge>not accepting</Badge>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
