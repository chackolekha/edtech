"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnCls, btnSecondary, cardCls, inputCls } from "@/components/ui";

interface MentorProfile {
  expertise: string | null;
  capacity: number;
  availability: string | null;
  accepting_requests: boolean;
  topics: string[];
  session_minutes: number;
  timezone: string;
  meeting_format: string | null;
}

interface Profile {
  user_id: string;
  slug: string;
  display_name: string;
  headline: string | null;
  bio: string | null;
  location: string | null;
  professional_status: string | null;
  current_title: string | null;
  current_org: string | null;
  years_experience: number | null;
  skills: string[];
  skill_details: { name: string; level: number }[];
  experiences: {
    id: string; kind: string; title: string; organization: string | null;
    start_date: string | null; end_date: string | null; is_current: boolean;
    description: string | null;
  }[];
  mentor_profile: MentorProfile | null;
}

interface Slot {
  id: string;
  starts_at: string;
  ends_at: string;
}

const EXPERIENCE_KINDS: Record<string, string> = {
  work: "Work", internship: "Internship", volunteering: "Volunteering",
};

export default function MentorDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [msg, setMsg] = useState("");
  const [topic, setTopic] = useState("");
  const [requestSent, setRequestSent] = useState(false);
  const [booked, setBooked] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) {
      Promise.all([
        api.get<Profile>(`/profiles/${id}`),
        api.get<Slot[]>(`/mentors/${id}/slots`),
      ]).then(([p, s]) => { setProfile(p); setSlots(s); }).catch(setError);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user, id]);

  if (loading || !user) return <Loading />;
  if (error) return <ErrorBox error={error} />;
  if (!profile) return <Loading />;
  const mp = profile.mentor_profile;
  const isStudent = user.role === "student";

  async function sendRequest() {
    try {
      await api.post("/mentor-requests", { mentor_id: id, message: msg || null });
      setRequestSent(true);
    } catch (e) { setError(e); }
  }

  async function book(slotId: string) {
    setBusy(slotId);
    setError(null);
    try {
      await api.post(`/mentor-slots/${slotId}/book`, { topic: topic || null });
      setBooked((b) => ({ ...b, [slotId]: true }));
    } catch (e) { setError(e); } finally { setBusy(null); }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className={cardCls}>
        <h1 className="text-2xl font-bold">{profile.display_name}</h1>
        {profile.headline && <p className="mt-1 text-gray-600">{profile.headline}</p>}
        <p className="mt-1 text-sm text-gray-500">
          {[profile.location,
            [profile.current_title, profile.current_org].filter(Boolean).join(" at "),
            profile.years_experience != null ? `${profile.years_experience} yrs experience` : null,
          ].filter(Boolean).join(" · ")}
        </p>
        {profile.bio && <p className="mt-3 text-sm text-gray-700">{profile.bio}</p>}
        {mp?.expertise && <p className="mt-3 text-sm text-gray-700">{mp.expertise}</p>}
        {mp && mp.topics.length > 0 && (
          <div className="mt-3">
            <p className="text-sm font-medium text-gray-700">Coaching topics</p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {mp.topics.map((t) => <Badge key={t} color="blue">{t}</Badge>)}
            </div>
          </div>
        )}
        {profile.skill_details.length > 0 && (
          <div className="mt-3">
            <p className="text-sm font-medium text-gray-700">Skills</p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {profile.skill_details.map((s) => <Badge key={s.name}>{s.name} · {s.level}/5</Badge>)}
            </div>
          </div>
        )}
        {mp && (
          <p className="mt-3 text-xs text-gray-500">
            {mp.session_minutes}-min sessions
            {mp.meeting_format ? ` · ${mp.meeting_format}` : ""}
            {mp.timezone ? ` · ${mp.timezone}` : ""}
          </p>
        )}
        {profile.experiences.length > 0 && (
          <div className="mt-4 border-t border-gray-200 pt-3">
            <h2 className="text-sm font-semibold">Experience</h2>
            <ul className="mt-2 space-y-2">
              {profile.experiences.map((exp) => (
                <li key={exp.id} className="text-sm text-gray-700">
                  <span className="font-medium">{exp.title}</span>
                  {exp.organization ? ` · ${exp.organization}` : ""}
                  <span className="text-gray-500">
                    {` (${EXPERIENCE_KINDS[exp.kind] ?? exp.kind}${exp.start_date ? `, ${exp.start_date}` : ""}–${exp.is_current ? "present" : exp.end_date ?? "?"})`}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {isStudent && (
        <div className={cardCls}>
          <h2 className="font-semibold">Book a session</h2>
          <input className={`${inputCls} mt-2`} placeholder="What do you want to cover? (topic)"
            value={topic} onChange={(e) => setTopic(e.target.value)} />
          {slots.length === 0 ? (
            <p className="mt-3 text-sm text-gray-500">No open slots right now.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {slots.map((s) => (
                <li key={s.id} className="flex items-center justify-between rounded-md border border-gray-200 p-2.5">
                  <span className="text-sm">
                    {new Date(s.starts_at).toLocaleString()} —{" "}
                    {new Date(s.ends_at).toLocaleTimeString()}
                  </span>
                  {booked[s.id] ? (
                    <Badge color="green">requested</Badge>
                  ) : (
                    <button onClick={() => book(s.id)} disabled={busy === s.id}
                      className={btnSecondary}>
                      {busy === s.id ? "Booking…" : "Book"}
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {isStudent && mp?.accepting_requests && (
        <div className={cardCls}>
          <h2 className="font-semibold">Request mentorship</h2>
          {requestSent ? (
            <Badge color="green">request sent</Badge>
          ) : (
            <div className="mt-2 flex gap-2">
              <input className={inputCls} placeholder="Message (optional)" value={msg}
                onChange={(e) => setMsg(e.target.value)} />
              <button onClick={sendRequest} className={btnCls}>Request</button>
            </div>
          )}
        </div>
      )}
      {isStudent && mp && !mp.accepting_requests && (
        <Empty>This mentor is not accepting new mentorship requests.</Empty>
      )}
      <ErrorBox error={error} />
    </div>
  );
}
