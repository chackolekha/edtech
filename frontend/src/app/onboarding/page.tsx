"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { ErrorBox, Field, Loading, btnCls, cardCls, inputCls } from "@/components/ui";

const PROFESSIONAL_STATUSES: [string, string][] = [
  ["student", "Student"],
  ["recent_graduate", "Recent graduate"],
  ["employed", "Employed"],
  ["seeking", "Seeking opportunities"],
  ["freelance", "Freelance / independent"],
];

const PURPOSES: [string, string][] = [
  ["find_projects", "Find projects"],
  ["find_mentor", "Find a mentor"],
  ["join_communities", "Join communities"],
  ["learn_skills", "Learn new skills"],
  ["build_portfolio", "Build my portfolio"],
];

export default function OnboardingPage() {
  const { user, loading, refresh } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    display_name: "", headline: "", bio: "", location: "", phone: "",
    college: "", graduation_year: "", degree: "", field_of_study: "",
    academic_year: "", gpa: "", academic_summary: "",
    professional_status: "", current_title: "", current_org: "", years_experience: "",
    portfolio_url: "", linkedin_url: "", github_url: "",
    skills: "", interests: "", purpose_note: "",
    expertise: "", capacity: "3", availability: "",
  });
  const [purposes, setPurposes] = useState<string[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  if (loading || !user) return <Loading />;
  const isMentor = user.role === "mentor";

  function set(k: string, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  function togglePurpose(value: string) {
    setPurposes((ps) => ps.includes(value) ? ps.filter((p) => p !== value) : [...ps, value]);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post("/onboarding", {
        display_name: form.display_name,
        headline: form.headline || null,
        bio: form.bio || null,
        location: form.location || null,
        phone: form.phone || null,
        college: form.college || null,
        degree: form.degree || null,
        field_of_study: form.field_of_study || null,
        academic_year: form.academic_year || null,
        gpa: form.gpa || null,
        academic_summary: form.academic_summary || null,
        graduation_year: form.graduation_year ? Number(form.graduation_year) : null,
        professional_status: form.professional_status || null,
        current_title: form.current_title || null,
        current_org: form.current_org || null,
        years_experience: form.years_experience ? Number(form.years_experience) : null,
        portfolio_url: form.portfolio_url || null,
        linkedin_url: form.linkedin_url || null,
        github_url: form.github_url || null,
        skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean)
          .map((name) => ({ name, level: 3 })),
        interests: form.interests.split(",").map((s) => s.trim()).filter(Boolean),
        purposes,
        purpose_note: form.purpose_note || null,
        expertise: isMentor ? form.expertise || null : null,
        capacity: isMentor ? Number(form.capacity) || 3 : 3,
        availability: isMentor ? form.availability || null : null,
      });
      await refresh();
      router.push("/");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg py-8">
      <div className={cardCls}>
        <h1 className="text-xl font-bold">Set up your profile</h1>
        <form onSubmit={submit} className="mt-4 space-y-6">
          <section className="space-y-4">
            <h2 className="border-b border-gray-200 pb-1 font-semibold">Personal</h2>
            <Field label="Display name *">
              <input className={inputCls} required value={form.display_name}
                onChange={(e) => set("display_name", e.target.value)} />
            </Field>
            <Field label="Headline">
              <input className={inputCls} placeholder="e.g. CS junior, aspiring backend dev"
                value={form.headline} onChange={(e) => set("headline", e.target.value)} />
            </Field>
            <Field label="Bio">
              <textarea className={inputCls} rows={3} value={form.bio}
                onChange={(e) => set("bio", e.target.value)} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Location">
                <input className={inputCls} placeholder="e.g. Bengaluru" value={form.location}
                  onChange={(e) => set("location", e.target.value)} />
              </Field>
              <Field label="Phone (private)">
                <input className={inputCls} value={form.phone}
                  onChange={(e) => set("phone", e.target.value)} />
              </Field>
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="border-b border-gray-200 pb-1 font-semibold">Education</h2>
            <div className="grid grid-cols-2 gap-3">
              <Field label="College / university">
                <input className={inputCls} value={form.college}
                  onChange={(e) => set("college", e.target.value)} />
              </Field>
              <Field label="Graduation year">
                <input className={inputCls} type="number" value={form.graduation_year}
                  onChange={(e) => set("graduation_year", e.target.value)} />
              </Field>
              <Field label="Degree">
                <input className={inputCls} placeholder="e.g. Bachelor of Science" value={form.degree}
                  onChange={(e) => set("degree", e.target.value)} />
              </Field>
              <Field label="Major / field of study">
                <input className={inputCls} value={form.field_of_study}
                  onChange={(e) => set("field_of_study", e.target.value)} />
              </Field>
              <Field label="Current academic year">
                <input className={inputCls} placeholder="e.g. Year 2" value={form.academic_year}
                  onChange={(e) => set("academic_year", e.target.value)} />
              </Field>
              <Field label="GPA / grade (include scale)">
                <input className={inputCls} placeholder="e.g. 3.8 / 4.0" value={form.gpa}
                  onChange={(e) => set("gpa", e.target.value)} />
              </Field>
            </div>
            <Field label="Academic achievements, coursework, or certifications">
              <textarea className={inputCls} rows={3} value={form.academic_summary}
                onChange={(e) => set("academic_summary", e.target.value)} />
            </Field>
          </section>

          <section className="space-y-4">
            <h2 className="border-b border-gray-200 pb-1 font-semibold">Professional</h2>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Current status">
                <select className={inputCls} value={form.professional_status}
                  onChange={(e) => set("professional_status", e.target.value)}>
                  <option value="">Select…</option>
                  {PROFESSIONAL_STATUSES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </Field>
              <Field label="Years of experience">
                <input className={inputCls} type="number" min="0" max="60" step="0.5"
                  value={form.years_experience}
                  onChange={(e) => set("years_experience", e.target.value)} />
              </Field>
              <Field label="Current role / title">
                <input className={inputCls} placeholder="e.g. SDE Intern" value={form.current_title}
                  onChange={(e) => set("current_title", e.target.value)} />
              </Field>
              <Field label="Current organization">
                <input className={inputCls} value={form.current_org}
                  onChange={(e) => set("current_org", e.target.value)} />
              </Field>
            </div>
            <Field label="Skills (comma-separated)">
              <input className={inputCls} placeholder="Python, Figma, SQL"
                value={form.skills} onChange={(e) => set("skills", e.target.value)} />
            </Field>
            <Field label="Interests (comma-separated)">
              <input className={inputCls} placeholder="AI, climate tech, fintech"
                value={form.interests} onChange={(e) => set("interests", e.target.value)} />
            </Field>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <Field label="Portfolio URL">
                <input className={inputCls} type="url" value={form.portfolio_url}
                  onChange={(e) => set("portfolio_url", e.target.value)} />
              </Field>
              <Field label="LinkedIn URL">
                <input className={inputCls} type="url" value={form.linkedin_url}
                  onChange={(e) => set("linkedin_url", e.target.value)} />
              </Field>
              <Field label="GitHub URL">
                <input className={inputCls} type="url" value={form.github_url}
                  onChange={(e) => set("github_url", e.target.value)} />
              </Field>
            </div>
            <p className="text-xs text-gray-500">You can add detailed work experience entries from your profile page after onboarding.</p>
          </section>

          <section className="space-y-4">
            <h2 className="border-b border-gray-200 pb-1 font-semibold">Purpose of joining</h2>
            <p className="text-sm text-gray-500">Private — only visible to you and platform admins.</p>
            <div className="flex flex-wrap gap-3">
              {PURPOSES.map(([v, l]) => (
                <label key={v} className="flex items-center gap-1.5 text-sm text-gray-700">
                  <input type="checkbox" checked={purposes.includes(v)}
                    onChange={() => togglePurpose(v)} />
                  {l}
                </label>
              ))}
            </div>
            <Field label="Anything else you want us to know (private)">
              <textarea className={inputCls} rows={3} value={form.purpose_note}
                onChange={(e) => set("purpose_note", e.target.value)} />
            </Field>
          </section>

          {isMentor && (
            <section className="space-y-4">
              <h2 className="border-b border-gray-200 pb-1 font-semibold">Mentor details</h2>
              <Field label="Expertise">
                <textarea className={inputCls} rows={2} value={form.expertise}
                  onChange={(e) => set("expertise", e.target.value)} />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Mentee capacity">
                  <input className={inputCls} type="number" min={1} value={form.capacity}
                    onChange={(e) => set("capacity", e.target.value)} />
                </Field>
                <Field label="Availability">
                  <input className={inputCls} placeholder="Weekday evenings"
                    value={form.availability} onChange={(e) => set("availability", e.target.value)} />
                </Field>
              </div>
            </section>
          )}
          <ErrorBox error={error} />
          <button className={btnCls} disabled={busy}>
            {busy ? "Saving…" : "Save profile"}
          </button>
        </form>
      </div>
    </div>
  );
}
