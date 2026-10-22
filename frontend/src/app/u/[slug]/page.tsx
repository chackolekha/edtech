"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Badge, Empty, ErrorBox, Loading, cardCls } from "@/components/ui";

interface Experience {
  id: string;
  kind: string;
  title: string;
  organization: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
}

interface Profile {
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
  professional_status: string | null;
  current_title: string | null;
  current_org: string | null;
  years_experience: number | null;
  skills: string[];
  skill_details: { name: string; level: number }[];
  interests: string[];
  experiences: Experience[];
  role: string;
}

const PROFESSIONAL_STATUSES: Record<string, string> = {
  student: "Student",
  recent_graduate: "Recent graduate",
  employed: "Employed",
  seeking: "Seeking opportunities",
  freelance: "Freelance / independent",
};

const EXPERIENCE_KINDS: Record<string, string> = {
  work: "Work",
  internship: "Internship",
  volunteering: "Volunteering",
};

interface Item {
  id: string;
  title: string;
  summary: string | null;
  skills: string[];
  published_at: string | null;
}

export default function PublicProfilePage() {
  const { slug } = useParams<{ slug: string }>();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    Promise.all([
      api.get<Profile>(`/u/${slug}`),
      api.get<Item[]>(`/u/${slug}/portfolio`),
    ])
      .then(([p, i]) => { setProfile(p); setItems(i); })
      .catch(setError);
  }, [slug]);

  if (error) return <ErrorBox error={error} />;
  if (!profile) return <Loading />;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className={cardCls}>
        <h1 className="text-2xl font-bold">{profile.display_name}</h1>
        {profile.headline && <p className="mt-1 text-gray-600">{profile.headline}</p>}
        <p className="mt-1 text-sm text-gray-500">
          {[profile.location, profile.college,
            profile.graduation_year ? `Class of ${profile.graduation_year}` : null]
            .filter(Boolean).join(" · ")}
        </p>
        {profile.bio && <p className="mt-3 text-sm text-gray-700">{profile.bio}</p>}
        {(profile.degree || profile.field_of_study || profile.academic_year || profile.gpa || profile.academic_summary) && (
          <div className="mt-3 rounded-lg bg-gray-50 p-3">
            <h2 className="text-sm font-semibold">Education</h2>
            <p className="mt-1 text-sm text-gray-700">
              {[profile.degree, profile.field_of_study, profile.academic_year].filter(Boolean).join(" · ")}
              {profile.gpa ? ` · GPA / grade: ${profile.gpa}` : ""}
            </p>
            {profile.academic_summary && <p className="mt-2 whitespace-pre-wrap text-sm text-gray-700">{profile.academic_summary}</p>}
          </div>
        )}
        {(profile.professional_status || profile.current_title || profile.years_experience != null || profile.experiences.length > 0) && (
          <div className="mt-3 rounded-lg bg-gray-50 p-3">
            <h2 className="text-sm font-semibold">Professional</h2>
            <p className="mt-1 text-sm text-gray-700">
              {[
                profile.professional_status ? PROFESSIONAL_STATUSES[profile.professional_status] ?? profile.professional_status : null,
                [profile.current_title, profile.current_org].filter(Boolean).join(" at "),
                profile.years_experience != null ? `${profile.years_experience} yrs experience` : null,
              ].filter(Boolean).join(" · ")}
            </p>
            {profile.experiences.length > 0 && (
              <ul className="mt-2 space-y-2">
                {profile.experiences.map((exp) => (
                  <li key={exp.id} className="text-sm text-gray-700">
                    <span className="font-medium">{exp.title}</span>
                    {exp.organization ? ` · ${exp.organization}` : ""}
                    <span className="text-gray-500">
                      {` (${EXPERIENCE_KINDS[exp.kind] ?? exp.kind}${exp.start_date ? `, ${exp.start_date}` : ""}–${exp.is_current ? "present" : exp.end_date ?? "?"})`}
                    </span>
                    {exp.description && <p className="text-gray-600">{exp.description}</p>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
        <h2 className="mt-4 text-sm font-medium text-gray-700">Skills</h2>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {profile.skill_details.map((s) => <Badge key={s.name}>{s.name} · {s.level}/5</Badge>)}
        </div>
        <div className="mt-3 flex flex-wrap gap-3 text-sm">
          {profile.portfolio_url && <a className="text-blue-600 underline" href={profile.portfolio_url} target="_blank" rel="noreferrer">Portfolio</a>}
          {profile.linkedin_url && <a className="text-blue-600 underline" href={profile.linkedin_url} target="_blank" rel="noreferrer">LinkedIn</a>}
          {profile.github_url && <a className="text-blue-600 underline" href={profile.github_url} target="_blank" rel="noreferrer">GitHub</a>}
        </div>
      </div>
      <h2 className="font-semibold">Portfolio</h2>
      {items.length === 0 ? (
        <Empty>No published work yet.</Empty>
      ) : (
        items.map((it) => (
          <div key={it.id} className={cardCls}>
            <h3 className="font-semibold">{it.title}</h3>
            {it.summary && <p className="mt-1 text-sm text-gray-600">{it.summary}</p>}
            <div className="mt-2 flex flex-wrap gap-1.5">
              {it.skills.map((s) => <Badge key={s}>{s}</Badge>)}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
