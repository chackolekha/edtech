"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnCls, btnSecondary, cardCls, inputCls } from "@/components/ui";

export interface Listing {
  id: string;
  author_id: string;
  author_name: string | null;
  title: string;
  brief: string;
  category: string | null;
  required_skills: string[];
  team_size: number;
  duration_weeks: number | null;
  status: string;
  application_count: number;
  my_application_id: string | null;
}

export default function ListingsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Listing[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [q, setQ] = useState("");
  const [mine, setMine] = useState(false);

  async function load(query = "", mineOnly = mine) {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (mineOnly) params.set("mine", "true");
    setItems(await api.get<Listing[]>(`/listings?${params}`));
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load().catch(setError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  if (loading || !user) return <Loading />;

  const canPost =
    user.role === "admin" ||
    ((user.role === "provider" || user.role === "mentor") &&
      user.verification_status === "verified");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Project marketplace</h1>
        <div className="flex gap-2">
          {canPost && (
            <>
              <button
                onClick={() => { setMine(!mine); load(q, !mine).catch(setError); }}
                className={btnSecondary}
              >
                {mine ? "All listings" : "My listings"}
              </button>
              <Link href="/listings/new" className={btnCls}>Post a project</Link>
            </>
          )}
        </div>
      </div>
      <form onSubmit={(e) => { e.preventDefault(); load(q).catch(setError); }} className="flex max-w-md gap-2">
        <input className={inputCls} placeholder="Search projects…" value={q}
          onChange={(e) => setQ(e.target.value)} />
        <button className={btnSecondary}>Search</button>
      </form>
      <ErrorBox error={error} />
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty>No projects found.</Empty>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((l) => (
            <Link key={l.id} href={`/listings/${l.id}`} className={`${cardCls} block hover:border-blue-300`}>
              <div className="flex items-start justify-between gap-2">
                <h2 className="font-semibold">{l.title}</h2>
                <Badge color={l.status === "open" ? "green" : l.status === "draft" ? "yellow" : "gray"}>
                  {l.status}
                </Badge>
              </div>
              <p className="mt-1 line-clamp-2 text-sm text-gray-600">{l.brief}</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {l.required_skills.map((s) => <Badge key={s}>{s}</Badge>)}
              </div>
              <p className="mt-2 text-xs text-gray-500">
                {l.author_name} · team of {l.team_size}
                {l.duration_weeks ? ` · ${l.duration_weeks} weeks` : ""} · {l.application_count} applicants
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
