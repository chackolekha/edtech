"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ErrorBox, Field, Loading, btnCls, cardCls, inputCls } from "@/components/ui";

export default function NewListingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    title: "", brief: "", category: "", required_skills: "",
    team_size: "1", duration_weeks: "", publish: true,
    kind: "project", deliverables: "", level: "", hours_per_week: "",
  });
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  if (loading || !user) return <Loading />;

  const canPost =
    user.role === "admin" ||
    ((user.role === "provider" || user.role === "mentor") &&
      user.verification_status === "verified");

  if (!canPost) {
    return (
      <div className={cardCls}>
        <h1 className="text-lg font-semibold">Cannot post projects</h1>
        <p className="mt-2 text-sm text-gray-600">
          Only verified providers, mentors or admins can post project briefs.
          {user.verification_status === "pending" && " Your account is pending verification."}
        </p>
      </div>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const l = await api.post<{ id: string }>("/listings", {
        title: form.title,
        brief: form.brief,
        category: form.category || null,
        required_skills: form.required_skills.split(",").map((s) => s.trim()).filter(Boolean),
        team_size: Number(form.team_size) || 1,
        duration_weeks: form.duration_weeks ? Number(form.duration_weeks) : null,
        kind: form.kind,
        deliverables: form.deliverables || null,
        level: form.level || null,
        hours_per_week: form.hours_per_week ? Number(form.hours_per_week) : null,
        publish: form.publish,
      });
      router.push(`/listings/${l.id}`);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg">
      <div className={cardCls}>
        <h1 className="text-xl font-bold">Post a project</h1>
        <form onSubmit={submit} className="mt-4 space-y-4">
          <Field label="Title *">
            <input className={inputCls} required value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </Field>
          <Field label="Brief * (min 10 chars)">
            <textarea className={inputCls} rows={4} required minLength={10}
              value={form.brief} onChange={(e) => setForm({ ...form, brief: e.target.value })} />
          </Field>
          <Field label="Category">
            <input className={inputCls} placeholder="web, data, design…" value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })} />
          </Field>
          <Field label="Required skills (comma-separated)">
            <input className={inputCls} value={form.required_skills}
              onChange={(e) => setForm({ ...form, required_skills: e.target.value })} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Team size">
              <input className={inputCls} type="number" min={1} max={50} value={form.team_size}
                onChange={(e) => setForm({ ...form, team_size: e.target.value })} />
            </Field>
            <Field label="Duration (weeks)">
              <input className={inputCls} type="number" min={1} value={form.duration_weeks}
                onChange={(e) => setForm({ ...form, duration_weeks: e.target.value })} />
            </Field>
          </div>
          {user.role === "mentor" && (
            <Field label="Project type">
              <select className={inputCls} value={form.kind}
                onChange={(e) => setForm({ ...form, kind: e.target.value })}>
                <option value="project">Project (students run it)</option>
                <option value="guided_project">Guided project (you mentor the team)</option>
              </select>
              {form.kind === "guided_project" && (
                <p className="mt-1 text-xs text-gray-500">
                  You will be attached as the team&apos;s mentor when a team is formed.
                </p>
              )}
            </Field>
          )}
          <Field label="Expected deliverables / outcomes">
            <textarea className={inputCls} rows={2} value={form.deliverables}
              placeholder="e.g. Working prototype + demo + code repository"
              onChange={(e) => setForm({ ...form, deliverables: e.target.value })} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Level">
              <select className={inputCls} value={form.level}
                onChange={(e) => setForm({ ...form, level: e.target.value })}>
                <option value="">Any</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </Field>
            <Field label="Commitment (hrs/week)">
              <input className={inputCls} type="number" min={1} max={80} value={form.hours_per_week}
                onChange={(e) => setForm({ ...form, hours_per_week: e.target.value })} />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.publish}
              onChange={(e) => setForm({ ...form, publish: e.target.checked })} />
            Publish immediately
          </label>
          <ErrorBox error={error} />
          <button className={btnCls} disabled={busy}>
            {busy ? "Posting…" : "Post project"}
          </button>
        </form>
      </div>
    </div>
  );
}
