"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnCls, cardCls, inputCls } from "@/components/ui";

interface Community {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  member_count: number;
  is_member: boolean;
}

export default function CommunitiesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Community[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [q, setQ] = useState("");
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [creating, setCreating] = useState(false);

  const canCreate =
    user?.role === "admin" ||
    ((user?.role === "mentor" || user?.role === "provider") &&
      user?.verification_status === "verified");

  async function load(query = "") {
    try {
      setItems(await api.get<Community[]>(`/communities${query ? `?q=${encodeURIComponent(query)}` : ""}`));
    } catch (e) {
      setError(e);
    }
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  if (loading || !user) return <Loading />;

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await api.post("/communities", { name, description: desc || null });
      setName("");
      setDesc("");
      await load();
    } catch (err) {
      setError(err);
    } finally {
      setCreating(false);
    }
  }

  async function join(id: string) {
    await api.post(`/communities/${id}/join`);
    await load(q);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Communities</h1>
        <form onSubmit={(e) => { e.preventDefault(); load(q); }} className="flex gap-2">
          <input className={inputCls} placeholder="Search…" value={q}
            onChange={(e) => setQ(e.target.value)} />
          <button className={btnCls}>Search</button>
        </form>
      </div>
      <ErrorBox error={error} />
      {canCreate && (
        <form onSubmit={create} className={`${cardCls} flex flex-wrap items-end gap-3`}>
          <input className={`${inputCls} max-w-xs`} placeholder="New community name"
            required value={name} onChange={(e) => setName(e.target.value)} />
          <input className={`${inputCls} flex-1`} placeholder="Description"
            value={desc} onChange={(e) => setDesc(e.target.value)} />
          <button className={btnCls} disabled={creating}>Create</button>
        </form>
      )}
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty>No communities yet.</Empty>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((c) => (
            <div key={c.id} className={cardCls}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <Link href={`/communities/${c.id}`} className="font-semibold text-accent hover:underline">
                    {c.name}
                  </Link>
                  <p className="mt-1 text-sm text-gray-600">{c.description}</p>
                </div>
                {c.is_member ? (
                  <Badge color="green">member</Badge>
                ) : (
                  <button onClick={() => join(c.id)} className={btnCls}>Join</button>
                )}
              </div>
              <p className="mt-2 text-xs text-gray-500">{c.member_count} members</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
