"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnCls, cardCls, inputCls } from "@/components/ui";
import type { Training } from "../page";

interface Lesson {
  id: string;
  title: string;
  content: string | null;
  points: number;
  completed: boolean;
}

interface Enrollment {
  id: string;
  status: string;
  score: number;
  progress_pct: number;
}

interface Detail extends Training {
  lessons: Lesson[];
  my_enrollment: Enrollment | null;
}

export default function TrainingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [t, setT] = useState<Detail | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [lessonTitle, setLessonTitle] = useState("");

  async function load() {
    setT(await api.get<Detail>(`/trainings/${id}`));
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load().catch(setError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user, id]);

  if (loading || !user) return <Loading />;
  if (error) return <ErrorBox error={error} />;
  if (!t) return <Loading />;

  const isAuthor = t.author_id === user.id || user.role === "admin";
  const enrollment = t.my_enrollment;

  async function enroll() {
    try {
      await api.post(`/trainings/${id}/enroll`);
      await load();
    } catch (e) {
      setError(e);
    }
  }

  async function completeLesson(lessonId: string) {
    if (!enrollment) return;
    await api.post(`/enrollments/${enrollment.id}/lessons/${lessonId}/complete`);
    await load();
  }

  async function addLesson(e: React.FormEvent) {
    e.preventDefault();
    await api.post(`/trainings/${id}/lessons`, { title: lessonTitle, points: 10 });
    setLessonTitle("");
    await load();
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className={cardCls}>
        <div className="flex items-start justify-between gap-3">
          <h1 className="text-2xl font-bold">{t.title}</h1>
          <Badge color={t.is_paid ? "yellow" : "green"}>
            {t.is_paid ? `$${(t.price_cents / 100).toFixed(2)}` : "free"}
          </Badge>
        </div>
        <p className="mt-1 text-sm text-gray-500">
          by {t.author_name} · pass at {t.pass_score}%
        </p>
        <p className="mt-3 whitespace-pre-wrap text-gray-800">{t.description}</p>
        {user.role === "student" && !enrollment && (
          <button onClick={enroll} className={`${btnCls} mt-4`}>
            Enroll{t.is_paid ? ` ($${(t.price_cents / 100).toFixed(2)})` : ""}
          </button>
        )}
        {enrollment && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm">
              <Badge color={enrollment.status === "completed" ? "green" : "blue"}>
                {enrollment.status}
              </Badge>
              <span className="text-gray-600">
                Score: {enrollment.score} · {enrollment.progress_pct}% complete
              </span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-gray-200">
              <div className="h-2 rounded-full bg-accent"
                style={{ width: `${enrollment.progress_pct}%` }} />
            </div>
          </div>
        )}
      </div>

      <div className={cardCls}>
        <h2 className="font-semibold">Lessons ({t.lessons.length})</h2>
        {isAuthor && (
          <form onSubmit={addLesson} className="mt-2 flex gap-2">
            <input className={inputCls} placeholder="New lesson title" required
              value={lessonTitle} onChange={(e) => setLessonTitle(e.target.value)} />
            <button className={btnCls}>Add</button>
          </form>
        )}
        <ul className="mt-3 space-y-2">
          {t.lessons.length === 0 && <Empty>No lessons yet.</Empty>}
          {t.lessons.map((l) => (
            <li key={l.id} className="flex items-center justify-between rounded-md border border-gray-200 p-3 text-sm">
              <div>
                <span className={l.completed ? "font-medium text-green-700" : "font-medium"}>
                  {l.title}
                </span>
                <span className="ml-2 text-xs text-gray-500">{l.points} pts</span>
                {l.content && <p className="mt-1 text-xs text-gray-600">{l.content}</p>}
              </div>
              {enrollment && !l.completed && enrollment.status !== "completed" && (
                <button onClick={() => completeLesson(l.id)} className={btnCls}>
                  Complete
                </button>
              )}
              {l.completed && <Badge color="green">done</Badge>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
