"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, ErrorBox, Field, Loading, btnCls, btnSecondary, cardCls, inputCls } from "@/components/ui";

interface SkillDetail {
  name: string;
  level: number;
}

interface Experience {
  id?: string;
  kind: string;
  title: string;
  organization: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  position?: number;
}

interface Profile {
  user_id: string;
  slug: string;
  display_name: string;
  headline: string | null;
  bio: string | null;
  college: string | null;
  degree: string | null;
  field_of_study: string | null;
  academic_year: string | null;
  gpa: string | null;
  academic_summary: string | null;
  graduation_year: number | null;
  portfolio_url: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  location: string | null;
  phone: string | null;
  professional_status: string | null;
  current_title: string | null;
  current_org: string | null;
  years_experience: number | null;
  purposes: string[];
  purpose_note: string | null;
  visibility: "public" | "private";
  role: string;
  verification_status: string;
  skills: string[];
  skill_details: SkillDetail[];
  interests: string[];
  experiences: Experience[];
}

const PROFESSIONAL_STATUSES: [string, string][] = [
  ["student", "Student"],
  ["recent_graduate", "Recent graduate"],
  ["employed", "Employed"],
  ["seeking", "Seeking opportunities"],
  ["freelance", "Freelance / independent"],
];

const EXPERIENCE_KINDS: [string, string][] = [
  ["work", "Work"],
  ["internship", "Internship"],
  ["volunteering", "Volunteering"],
];

const PURPOSES: [string, string][] = [
  ["find_projects", "Find projects"],
  ["find_mentor", "Find a mentor"],
  ["join_communities", "Join communities"],
  ["learn_skills", "Learn new skills"],
  ["build_portfolio", "Build my portfolio"],
];

function labelOf(options: [string, string][], value: string | null): string {
  return options.find(([v]) => v === value)?.[1] ?? value ?? "";
}

function emptyExperience(): Experience {
  return { kind: "work", title: "", organization: null, start_date: null, end_date: null, is_current: false, description: null };
}

export default function MePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Profile | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user?.onboarding_complete) {
      api.get<Profile>("/me/profile").then(setProfile).catch(setError);
    }
  }, [loading, user, router]);

  if (loading || !user) return <Loading />;
  if (!user.onboarding_complete) {
    router.push("/onboarding");
    return <Loading />;
  }
  if (!profile) return error ? <ErrorBox error={error} /> : <Loading />;

  function updateDraft(key: keyof Profile, value: string | number | string[] | null) {
    setDraft((current) => current ? { ...current, [key]: value } : current);
  }

  function updateExperience(index: number, patch: Partial<Experience>) {
    setDraft((current) => current ? {
      ...current,
      experiences: current.experiences.map((e, i) => i === index ? { ...e, ...patch } : e),
    } : current);
  }

  async function toggleVisibility() {
    if (!profile) return;
    const next = profile.visibility === "public" ? "private" : "public";
    const updated = await api.patch<Profile>("/me/profile", { visibility: next });
    setProfile(updated);
  }

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    if (!draft) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api.patch<Profile>("/me/profile", {
        display_name: draft.display_name,
        headline: draft.headline || null,
        bio: draft.bio || null,
        location: draft.location || null,
        phone: draft.phone || null,
        college: draft.college || null,
        degree: draft.degree || null,
        field_of_study: draft.field_of_study || null,
        academic_year: draft.academic_year || null,
        gpa: draft.gpa || null,
        academic_summary: draft.academic_summary || null,
        graduation_year: draft.graduation_year || null,
        professional_status: draft.professional_status || null,
        current_title: draft.current_title || null,
        current_org: draft.current_org || null,
        years_experience: draft.years_experience,
        portfolio_url: draft.portfolio_url || null,
        linkedin_url: draft.linkedin_url || null,
        github_url: draft.github_url || null,
        purposes: draft.purposes,
        purpose_note: draft.purpose_note || null,
      });
      await api.put<Profile>("/me/experiences", {
        experiences: draft.experiences
          .filter((x) => x.title.trim())
          .map((x) => ({
            kind: x.kind, title: x.title.trim(),
            organization: x.organization || null,
            start_date: x.start_date || null,
            end_date: x.is_current ? null : (x.end_date || null),
            is_current: x.is_current,
            description: x.description || null,
          })),
      });
      await api.put<Profile>("/me/skills", {
        skills: draft.skill_details.filter((skill) => skill.name.trim()).map((skill) => ({
          name: skill.name.trim(), level: skill.level,
        })),
      });
      const interestsUpdated = await api.put<Profile>("/me/interests", { interests: draft.interests });
      setProfile(interestsUpdated ?? updated);
      setDraft(null);
      setEditing(false);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  if (editing && draft) {
    return (
      <div className="mx-auto max-w-3xl">
        <form onSubmit={saveProfile} className={`${cardCls} space-y-6`}>
          <div>
            <h1 className="text-2xl font-bold">Edit student profile</h1>
            <p className="mt-1 text-sm text-gray-600">Keep your four profile sections up to date.</p>
          </div>

          <section className="space-y-4">
            <h2 className="border-b border-gray-200 pb-1 font-semibold">Personal</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Display name">
                <input className={inputCls} required value={draft.display_name}
                  onChange={(e) => updateDraft("display_name", e.target.value)} />
              </Field>
              <Field label="Headline">
                <input className={inputCls} value={draft.headline ?? ""}
                  onChange={(e) => updateDraft("headline", e.target.value)} placeholder="e.g. Computer science student" />
              </Field>
              <Field label="Location">
                <input className={inputCls} value={draft.location ?? ""}
                  onChange={(e) => updateDraft("location", e.target.value)} placeholder="e.g. Bengaluru" />
              </Field>
              <Field label="Phone (private — only you and admins can see it)">
                <input className={inputCls} value={draft.phone ?? ""}
                  onChange={(e) => updateDraft("phone", e.target.value)} />
              </Field>
            </div>
            <Field label="About me">
              <textarea className={inputCls} rows={4} value={draft.bio ?? ""}
                onChange={(e) => updateDraft("bio", e.target.value)} />
            </Field>
          </section>

          <section className="space-y-4">
            <h2 className="border-b border-gray-200 pb-1 font-semibold">Education</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="College / university">
                <input className={inputCls} value={draft.college ?? ""}
                  onChange={(e) => updateDraft("college", e.target.value)} />
              </Field>
              <Field label="Degree">
                <input className={inputCls} value={draft.degree ?? ""}
                  onChange={(e) => updateDraft("degree", e.target.value)} placeholder="e.g. Bachelor of Science" />
              </Field>
              <Field label="Major / field of study">
                <input className={inputCls} value={draft.field_of_study ?? ""}
                  onChange={(e) => updateDraft("field_of_study", e.target.value)} />
              </Field>
              <Field label="Current academic year">
                <input className={inputCls} value={draft.academic_year ?? ""}
                  onChange={(e) => updateDraft("academic_year", e.target.value)} placeholder="e.g. Year 2" />
              </Field>
              <Field label="GPA / grade (include scale)">
                <input className={inputCls} value={draft.gpa ?? ""}
                  onChange={(e) => updateDraft("gpa", e.target.value)} placeholder="e.g. 3.8 / 4.0" />
              </Field>
              <Field label="Expected graduation year">
                <input className={inputCls} type="number" min="1950" max="2100"
                  value={draft.graduation_year ?? ""}
                  onChange={(e) => setDraft({ ...draft, graduation_year: e.target.value ? Number(e.target.value) : null })} />
              </Field>
            </div>
            <Field label="Academic achievements, coursework, or certifications">
              <textarea className={inputCls} rows={4} value={draft.academic_summary ?? ""}
                onChange={(e) => updateDraft("academic_summary", e.target.value)} />
            </Field>
          </section>

          <section className="space-y-4">
            <h2 className="border-b border-gray-200 pb-1 font-semibold">Professional</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Current status">
                <select className={inputCls} value={draft.professional_status ?? ""}
                  onChange={(e) => updateDraft("professional_status", e.target.value || null)}>
                  <option value="">Select…</option>
                  {PROFESSIONAL_STATUSES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </Field>
              <Field label="Years of experience">
                <input className={inputCls} type="number" min="0" max="60" step="0.5"
                  value={draft.years_experience ?? ""}
                  onChange={(e) => setDraft({ ...draft, years_experience: e.target.value ? Number(e.target.value) : null })} />
              </Field>
              <Field label="Current role / title">
                <input className={inputCls} value={draft.current_title ?? ""}
                  onChange={(e) => updateDraft("current_title", e.target.value)} placeholder="e.g. SDE Intern" />
              </Field>
              <Field label="Current organization">
                <input className={inputCls} value={draft.current_org ?? ""}
                  onChange={(e) => updateDraft("current_org", e.target.value)} />
              </Field>
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-700">Work experience</h3>
                <button type="button" className={btnSecondary}
                  onClick={() => setDraft({ ...draft, experiences: [...draft.experiences, emptyExperience()] })}>
                  Add experience
                </button>
              </div>
              <div className="space-y-3">
                {draft.experiences.map((exp, index) => (
                  <div key={index} className="rounded-lg border border-gray-200 p-3 space-y-2">
                    <div className="grid gap-2 sm:grid-cols-[140px_1fr_1fr]">
                      <select className={inputCls} aria-label="Experience type" value={exp.kind}
                        onChange={(e) => updateExperience(index, { kind: e.target.value })}>
                        {EXPERIENCE_KINDS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                      </select>
                      <input className={inputCls} aria-label="Role title" placeholder="Title (required)" required
                        value={exp.title} onChange={(e) => updateExperience(index, { title: e.target.value })} />
                      <input className={inputCls} aria-label="Organization" placeholder="Organization"
                        value={exp.organization ?? ""} onChange={(e) => updateExperience(index, { organization: e.target.value })} />
                    </div>
                    <div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                      <input className={inputCls} aria-label="Start date" placeholder="Start (YYYY-MM)" pattern="\d{4}-\d{2}"
                        value={exp.start_date ?? ""} onChange={(e) => updateExperience(index, { start_date: e.target.value })} />
                      <input className={inputCls} aria-label="End date" placeholder="End (YYYY-MM)" pattern="\d{4}-\d{2}"
                        disabled={exp.is_current}
                        value={exp.end_date ?? ""} onChange={(e) => updateExperience(index, { end_date: e.target.value })} />
                      <label className="flex items-center gap-1.5 text-sm text-gray-700">
                        <input type="checkbox" checked={exp.is_current}
                          onChange={(e) => updateExperience(index, { is_current: e.target.checked })} />
                        Current
                      </label>
                    </div>
                    <textarea className={inputCls} rows={2} aria-label="Description" placeholder="What you did"
                      value={exp.description ?? ""} onChange={(e) => updateExperience(index, { description: e.target.value })} />
                    <button type="button" className={btnSecondary} aria-label={`Remove ${exp.title || "experience"}`}
                      onClick={() => setDraft({ ...draft, experiences: draft.experiences.filter((_, i) => i !== index) })}>
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-700">Skills and proficiency</h3>
                <button type="button" className={btnSecondary}
                  onClick={() => setDraft({ ...draft, skill_details: [...draft.skill_details, { name: "", level: 3 }] })}>
                  Add skill
                </button>
              </div>
              <div className="space-y-2">
                {draft.skill_details.map((skill, index) => (
                  <div key={`${skill.name}-${index}`} className="grid grid-cols-[1fr_140px_auto] gap-2">
                    <input className={inputCls} aria-label="Skill name" placeholder="e.g. Python"
                      value={skill.name} onChange={(e) => setDraft({ ...draft, skill_details: draft.skill_details.map((s, i) => i === index ? { ...s, name: e.target.value } : s) })} />
                    <select className={inputCls} aria-label="Skill proficiency" value={skill.level}
                      onChange={(e) => setDraft({ ...draft, skill_details: draft.skill_details.map((s, i) => i === index ? { ...s, level: Number(e.target.value) } : s) })}>
                      <option value={1}>Beginner</option><option value={2}>Basic</option><option value={3}>Intermediate</option><option value={4}>Advanced</option><option value={5}>Expert</option>
                    </select>
                    <button type="button" className={btnSecondary} aria-label={`Remove ${skill.name || "skill"}`}
                      onClick={() => setDraft({ ...draft, skill_details: draft.skill_details.filter((_, i) => i !== index) })}>Remove</button>
                  </div>
                ))}
              </div>
            </div>
            <Field label="Interests (comma-separated)">
              <input className={inputCls} value={draft.interests.join(", ")}
                onChange={(e) => setDraft({ ...draft, interests: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} />
            </Field>
            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="Portfolio URL"><input className={inputCls} type="url" value={draft.portfolio_url ?? ""} onChange={(e) => updateDraft("portfolio_url", e.target.value)} /></Field>
              <Field label="LinkedIn URL"><input className={inputCls} type="url" value={draft.linkedin_url ?? ""} onChange={(e) => updateDraft("linkedin_url", e.target.value)} /></Field>
              <Field label="GitHub URL"><input className={inputCls} type="url" value={draft.github_url ?? ""} onChange={(e) => updateDraft("github_url", e.target.value)} /></Field>
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="border-b border-gray-200 pb-1 font-semibold">Purpose of joining</h2>
            <p className="text-sm text-gray-500">Private — only visible to you and platform admins.</p>
            <div className="flex flex-wrap gap-3">
              {PURPOSES.map(([v, l]) => (
                <label key={v} className="flex items-center gap-1.5 text-sm text-gray-700">
                  <input type="checkbox" checked={draft.purposes.includes(v)}
                    onChange={(e) => updateDraft("purposes", e.target.checked
                      ? [...draft.purposes, v]
                      : draft.purposes.filter((p) => p !== v))} />
                  {l}
                </label>
              ))}
            </div>
            <Field label="Anything else you want us to know (private)">
              <textarea className={inputCls} rows={3} value={draft.purpose_note ?? ""}
                onChange={(e) => updateDraft("purpose_note", e.target.value)} />
            </Field>
          </section>

          <ErrorBox error={error} />
          <div className="flex gap-2">
            <button className={btnCls} disabled={busy}>{busy ? "Saving…" : "Save profile"}</button>
            <button type="button" className={btnSecondary} onClick={() => { setDraft(null); setEditing(false); }}>Cancel</button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className={cardCls}>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{profile.display_name}</h1>
            {profile.headline && <p className="mt-1 text-gray-600">{profile.headline}</p>}
            <p className="mt-1 text-sm text-gray-500">
              {[profile.location, profile.college, profile.graduation_year ? `Class of ${profile.graduation_year}` : null]
                .filter(Boolean).join(" · ")}
            </p>
            <div className="mt-2 flex gap-2">
              <Badge color="blue">{profile.role}</Badge>
              <Badge color={profile.verification_status === "verified" ? "green" : "yellow"}>
                {profile.verification_status}
              </Badge>
              <Badge>{profile.visibility}</Badge>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => { setDraft({ ...profile }); setEditing(true); }} className={btnCls}>Edit profile</button>
            <button onClick={toggleVisibility} className={btnSecondary}>
              Make {profile.visibility === "public" ? "private" : "public"}
            </button>
          </div>
        </div>
        {profile.bio && <p className="mt-4 text-sm text-gray-700">{profile.bio}</p>}
        {profile.phone && <p className="mt-2 text-sm text-gray-500">Phone (private): {profile.phone}</p>}

        <div className="mt-5 border-t border-gray-200 pt-4">
          <h2 className="font-semibold">Education</h2>
          <p className="mt-1 text-sm text-gray-700">
            {[profile.degree, profile.field_of_study, profile.academic_year].filter(Boolean).join(" · ") || "Add your degree and area of study."}
          </p>
          {profile.gpa && <p className="mt-1 text-sm text-gray-600">GPA / grade: {profile.gpa}</p>}
          {profile.academic_summary && <p className="mt-2 whitespace-pre-wrap text-sm text-gray-700">{profile.academic_summary}</p>}
        </div>

        <div className="mt-5 border-t border-gray-200 pt-4">
          <h2 className="font-semibold">Professional</h2>
          <p className="mt-1 text-sm text-gray-700">
            {[labelOf(PROFESSIONAL_STATUSES, profile.professional_status),
              [profile.current_title, profile.current_org].filter(Boolean).join(" at "),
              profile.years_experience != null ? `${profile.years_experience} yrs experience` : null]
              .filter(Boolean).join(" · ") || "Add your professional status and experience."}
          </p>
          {profile.experiences.length > 0 && (
            <ul className="mt-3 space-y-2">
              {profile.experiences.map((exp) => (
                <li key={exp.id ?? exp.title} className="text-sm text-gray-700">
                  <span className="font-medium">{exp.title}</span>
                  {exp.organization ? ` · ${exp.organization}` : ""}
                  <span className="text-gray-500">
                    {` (${labelOf(EXPERIENCE_KINDS, exp.kind)}${exp.start_date ? `, ${exp.start_date}` : ""}–${exp.is_current ? "present" : exp.end_date ?? "?"})`}
                  </span>
                  {exp.description && <p className="text-gray-600">{exp.description}</p>}
                </li>
              ))}
            </ul>
          )}
          <div className="mt-4">
            <p className="text-sm font-medium text-gray-700">Skills</p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {profile.skill_details.map((s) => <Badge key={s.name}>{s.name} · {s.level}/5</Badge>)}
            </div>
          </div>
          <div className="mt-3">
            <p className="text-sm font-medium text-gray-700">Interests</p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {profile.interests.map((s) => <Badge key={s}>{s}</Badge>)}
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-3 text-sm">
            {profile.portfolio_url && <a className="text-blue-600 underline" href={profile.portfolio_url} target="_blank" rel="noreferrer">Portfolio</a>}
            {profile.linkedin_url && <a className="text-blue-600 underline" href={profile.linkedin_url} target="_blank" rel="noreferrer">LinkedIn</a>}
            {profile.github_url && <a className="text-blue-600 underline" href={profile.github_url} target="_blank" rel="noreferrer">GitHub</a>}
          </div>
        </div>

        <div className="mt-5 border-t border-gray-200 pt-4">
          <h2 className="font-semibold">Purpose of joining</h2>
          <p className="text-xs text-gray-500">Private — only visible to you and admins.</p>
          {profile.purposes.length > 0 ? (
            <div className="mt-1 flex flex-wrap gap-1.5">
              {profile.purposes.map((p) => <Badge key={p}>{labelOf(PURPOSES, p)}</Badge>)}
            </div>
          ) : <p className="mt-1 text-sm text-gray-600">Not set.</p>}
          {profile.purpose_note && <p className="mt-2 whitespace-pre-wrap text-sm text-gray-700">{profile.purpose_note}</p>}
        </div>

        <p className="mt-4 text-sm text-gray-500">
          Public profile:{" "}
          <a className="text-blue-600 underline" href={`/u/${profile.slug}`}>
            /u/{profile.slug}
          </a>
        </p>
      </div>
    </div>
  );
}
