"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnCls, btnSecondary, cardCls, inputCls } from "@/components/ui";

export interface Training {
  id: string;
  author_id: string;
  author_name: string | null;
  title: string;
  description: string | null;
  category: string | null;
  is_paid: boolean;
  price_cents: number;
  pass_score: number;
  lesson_count: number;
  enrollment_count: number;
}

export default function TrainingsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Training[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [q, setQ] = useState("");
  const [free, setFree] = useState<boolean | null>(null);

  async function load() {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (free !== null) params.set("free", String(free));
    setItems(await api.get<Training[]>(`/trainings?${params}`));
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load().catch(setError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user, free]);

  if (loading || !user) return <Loading />;

  const canAuthor =
    user.role === "admin" ||
    ((user.role === "provider" || user.role === "mentor") &&
      user.verification_status === "verified");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Trainings</h1>
        {canAuthor && <Link href="/trainings/new" className={btnCls}>Create training</Link>}
      </div>
      <div className="flex flex-wrap gap-2">
        <form onSubmit={(e) => { e.preventDefault(); load().catch(setError); }} className="flex gap-2">
          <input className={inputCls} placeholder="Search trainings…" value={q}
            onChange={(e) => setQ(e.target.value)} />
          <button className={btnSecondary}>Search</button>
        </form>
        <button onClick={() => setFree(free === true ? null : true)}
          className={free === true ? btnCls : btnSecondary}>Free</button>
        <button onClick={() => setFree(free === false ? null : false)}
          className={free === false ? btnCls : btnSecondary}>Paid</button>
      </div>
      <ErrorBox error={error} />
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty>No trainings found.</Empty>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((t) => (
            <Link key={t.id} href={`/trainings/${t.id}`} className={`${cardCls} block hover:border-blue-300`}>
              <div className="flex items-start justify-between gap-2">
                <h2 className="font-semibold">{t.title}</h2>
                <Badge color={t.is_paid ? "yellow" : "green"}>
                  {t.is_paid ? `$${(t.price_cents / 100).toFixed(2)}` : "free"}
                </Badge>
              </div>
              <p className="mt-1 line-clamp-2 text-sm text-gray-600">{t.description}</p>
              <p className="mt-2 text-xs text-gray-500">
                {t.lesson_count} lessons · pass at {t.pass_score}% · {t.enrollment_count} enrolled
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
