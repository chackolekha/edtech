"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Loading, cardCls } from "@/components/ui";

const ROLE_TAGLINES: Record<string, string> = {
  student: "Find projects, mentors and communities to grow your career.",
  mentor: "Share your expertise — coach students and guide real projects.",
  provider: "Post real-world briefs and discover emerging talent.",
  admin: "Verify members, moderate the platform, and track the pilot.",
};

const tiles = [
  { href: "/listings", title: "Find projects", desc: "Apply to real-world briefs" },
  { href: "/communities", title: "Communities", desc: "Discuss with peers" },
  { href: "/mentors", title: "Mentors", desc: "Get guidance from experts" },
  { href: "/trainings", title: "Trainings", desc: "Build skills, earn scores" },
  { href: "/workspaces", title: "Workspaces", desc: "Collaborate and deliver" },
  { href: "/portfolio", title: "Portfolio", desc: "Publish your work" },
];

export default function Home() {
  const { user, loading } = useAuth();
  if (loading) return <Loading />;

  if (!user) {
    return (
      <div className="relative overflow-hidden rounded-2xl border border-gray-200 bg-gradient-to-br from-accent-soft via-white to-white px-8 py-20 text-center">
        <div className="mx-auto max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-widest text-accent">
            Learn · Build · Mentor
          </p>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-gray-900">
            Learn by doing real projects
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-gray-600">
            Discover communities, find mentors, join project teams, earn feedback,
            and build a career-ready portfolio.
          </p>
          <div className="mt-8 flex justify-center gap-3">
            <Link href="/register"
              className="rounded-lg bg-accent px-6 py-3 font-medium text-white shadow-xs transition hover:bg-accent-strong">
              Get started
            </Link>
            <Link href="/login"
              className="rounded-lg border border-gray-300 bg-white px-6 py-3 font-medium text-gray-700 transition hover:bg-gray-50">
              Log in
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="rounded-2xl border border-gray-200 bg-gradient-to-r from-accent-soft to-white p-6">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">
          Welcome back{user.role === "student" ? ", keep building" : ""}
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          {ROLE_TAGLINES[user.role] ?? ""}
          {user.verification_status === "pending" && (
            <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
              verification pending
            </span>
          )}
          {!user.onboarding_complete && (
            <Link href="/onboarding" className="ml-3 font-medium text-accent underline">
              Finish onboarding →
            </Link>
          )}
        </p>
      </div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tiles.map((t) => (
          <Link key={t.href} href={t.href}
            className={`${cardCls} group block hover:border-accent`}>
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">{t.title}</h2>
              <span className="text-gray-300 transition group-hover:translate-x-0.5 group-hover:text-accent">
                →
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-600">{t.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
