"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnDanger, btnSecondary, cardCls, inputCls } from "@/components/ui";

interface Item {
  id: string;
  title: string;
  summary: string | null;
  skills: string[];
  is_published: boolean;
  published_at: string | null;
  workspace_id: string | null;
}

export default function PortfolioPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Item[] | null>(null);
  const [slug, setSlug] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");

  async function load() {
    setItems(await api.get<Item[]>("/portfolio/mine"));
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) {
      load().catch(setError);
      api.get<{ slug: string }>("/me/profile").then((p) => setSlug(p.slug)).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  if (loading || !user) return <Loading />;

  async function create(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/portfolio-items", { title, summary: summary || null });
    setTitle("");
    setSummary("");
    await load();
  }

  async function toggle(it: Item) {
    await api.post(`/portfolio-items/${it.id}/${it.is_published ? "unpublish" : "publish"}`);
    await load();
  }

  async function remove(id: string) {
    await api.del(`/portfolio-items/${id}`);
    await load();
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">My portfolio</h1>
        {slug && (
          <Link href={`/u/${slug}`} className="text-sm text-accent hover:underline">
            View public page →
          </Link>
        )}
      </div>
      <ErrorBox error={error} />
      <form onSubmit={create} className={`${cardCls} space-y-3`}>
        <h2 className="font-medium">Add portfolio item</h2>
        <input className={inputCls} placeholder="Title *" required value={title}
          onChange={(e) => setTitle(e.target.value)} />
        <textarea className={inputCls} rows={2} placeholder="Summary"
          value={summary} onChange={(e) => setSummary(e.target.value)} />
        <button className={btnSecondary}>Add item</button>
      </form>
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty>
          No portfolio items yet. They are created when projects complete, or add one above.
        </Empty>
      ) : (
        items.map((it) => (
          <div key={it.id} className={cardCls}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-semibold">{it.title}</h2>
                {it.summary && <p className="mt-1 text-sm text-gray-600">{it.summary}</p>}
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {it.skills.map((s) => <Badge key={s}>{s}</Badge>)}
                </div>
              </div>
              <Badge color={it.is_published ? "green" : "gray"}>
                {it.is_published ? "published" : "private"}
              </Badge>
            </div>
            <div className="mt-3 flex gap-2">
              <button onClick={() => toggle(it)} className={btnSecondary}>
                {it.is_published ? "Unpublish" : "Publish"}
              </button>
              <button onClick={() => remove(it.id)} className={btnDanger}>Delete</button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
