"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ErrorBox, Field, Loading, btnCls, cardCls, inputCls } from "@/components/ui";

export default function NewTrainingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    title: "", description: "", category: "",
    is_paid: false, price: "", pass_score: "70",
  });
  const [lessons, setLessons] = useState<{ title: string; points: string }[]>([
    { title: "", points: "10" },
  ]);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  if (loading || !user) return <Loading />;

  const canAuthor =
    user.role === "admin" ||
    ((user.role === "provider" || user.role === "mentor") &&
      user.verification_status === "verified");
  if (!canAuthor) {
    return (
      <div className={cardCls}>
        <p className="text-sm text-gray-600">
          Only verified providers, mentors or admins can author trainings.
        </p>
      </div>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const t = await api.post<{ id: string }>("/trainings", {
        title: form.title,
        description: form.description || null,
        category: form.category || null,
        is_paid: form.is_paid,
        price_cents: form.is_paid ? Math.round(Number(form.price || "0") * 100) : 0,
        pass_score: Number(form.pass_score) || 70,
      });
      for (const [i, l] of lessons.entries()) {
        if (!l.title.trim()) continue;
        await api.post(`/trainings/${t.id}/lessons`, {
          title: l.title, points: Number(l.points) || 10, position: i,
        });
      }
      router.push(`/trainings/${t.id}`);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg">
      <div className={cardCls}>
        <h1 className="text-xl font-bold">Create training</h1>
        <form onSubmit={submit} className="mt-4 space-y-4">
          <Field label="Title *">
            <input className={inputCls} required value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </Field>
          <Field label="Description">
            <textarea className={inputCls} rows={3} value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Category">
              <input className={inputCls} value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })} />
            </Field>
            <Field label="Pass score %">
              <input className={inputCls} type="number" min={1} max={100}
                value={form.pass_score}
                onChange={(e) => setForm({ ...form, pass_score: e.target.value })} />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_paid}
              onChange={(e) => setForm({ ...form, is_paid: e.target.checked })} />
            Paid training
          </label>
          {form.is_paid && (
            <Field label="Price (USD)">
              <input className={inputCls} type="number" min={0} step="0.01" value={form.price}
                onChange={(e) => setForm({ ...form, price: e.target.value })} />
            </Field>
          )}
          <div>
            <p className="text-sm font-medium text-gray-700">Lessons</p>
            {lessons.map((l, i) => (
              <div key={i} className="mt-2 flex gap-2">
                <input className={inputCls} placeholder={`Lesson ${i + 1} title`}
                  value={l.title}
                  onChange={(e) => {
                    const next = [...lessons];
                    next[i] = { ...l, title: e.target.value };
                    setLessons(next);
                  }} />
                <input className={inputCls} style={{ width: 90 }} type="number" min={0}
                  value={l.points} title="Points"
                  onChange={(e) => {
                    const next = [...lessons];
                    next[i] = { ...l, points: e.target.value };
                    setLessons(next);
                  }} />
              </div>
            ))}
            <button type="button" className="mt-2 text-sm text-blue-600 hover:underline"
              onClick={() => setLessons([...lessons, { title: "", points: "10" }])}>
              + Add lesson
            </button>
          </div>
          <ErrorBox error={error} />
          <button className={btnCls} disabled={busy}>
            {busy ? "Creating…" : "Create training"}
          </button>
        </form>
      </div>
    </div>
  );
}
