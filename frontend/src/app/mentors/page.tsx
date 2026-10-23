"use client";

import Link from "next/link";
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
  topics: string[];
  session_minutes: number | null;
  next_open_slot: string | null;
}

export default function MentorsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Mentor[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [q, setQ] = useState("");
  const [topic, setTopic] = useState("");

  async function load(query = "", topicQuery = "") {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (topicQuery) params.set("topic", topicQuery);
    setItems(await api.get<Mentor[]>(`/mentors?${params}`));
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load().catch(setError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  if (loading || !user) return <Loading />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Find a mentor</h1>
      </div>
      <form onSubmit={(e) => { e.preventDefault(); load(q, topic).catch(setError); }}
        className="flex max-w-xl gap-2">
        <input className={inputCls} placeholder="Search mentors…" value={q}
          onChange={(e) => setQ(e.target.value)} />
        <input className={inputCls} placeholder="Topic (e.g. interview)" value={topic}
          onChange={(e) => setTopic(e.target.value)} />
        <button className={btnCls}>Search</button>
      </form>
      <ErrorBox error={error} />
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty>No verified mentors found.</Empty>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((m) => (
            <div key={m.user_id} className={cardCls}>
              <h2 className="font-semibold">
                <Link href={`/mentors/${m.user_id}`} className="hover:underline">
                  {m.display_name}
                </Link>
              </h2>
              {m.headline && <p className="text-sm text-gray-600">{m.headline}</p>}
              {m.expertise && <p className="mt-1 text-sm text-gray-700">{m.expertise}</p>}
              {m.topics.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-gray-500">Coaching topics</p>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {m.topics.map((t) => <Badge key={t} color="blue">{t}</Badge>)}
                  </div>
                </div>
              )}
              <div className="mt-2 flex flex-wrap gap-1.5">
                {m.skills.map((s) => <Badge key={s}>{s}</Badge>)}
              </div>
              <p className="mt-2 text-xs text-gray-500">
                {m.session_minutes ? `${m.session_minutes}-min sessions` : ""}
                {m.next_open_slot
                  ? ` · next open: ${new Date(m.next_open_slot).toLocaleString()}`
                  : " · no open slots"}
              </p>
              {!m.accepting_requests && <Badge>not accepting requests</Badge>}
              <div className="mt-3">
                <Link href={`/mentors/${m.user_id}`} className={btnCls}>
                  View profile & book
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
