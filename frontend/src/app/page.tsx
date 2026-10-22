"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Loading, cardCls } from "@/components/ui";

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
      <div className="py-16 text-center">
        <h1 className="text-3xl font-bold">Learn by doing real projects</h1>
        <p className="mx-auto mt-3 max-w-xl text-gray-600">
          Discover communities, find mentors, join project teams, earn feedback,
          and build a career-ready portfolio.
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Link href="/register" className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700">
            Get started
          </Link>
          <Link href="/login" className="rounded-md border border-gray-300 px-5 py-2.5 font-medium text-gray-700 hover:bg-gray-50">
            Log in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Welcome back</h1>
      <p className="mt-1 text-sm text-gray-600">
        Role: <span className="font-medium">{user.role}</span>
        {user.verification_status === "pending" && (
          <span className="ml-2 rounded-full bg-yellow-100 px-2 py-0.5 text-xs text-yellow-800">
            verification pending
          </span>
        )}
        {!user.onboarding_complete && (
          <Link href="/onboarding" className="ml-3 text-blue-600 underline">
            Finish onboarding →
          </Link>
        )}
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tiles.map((t) => (
          <Link key={t.href} href={t.href} className={`${cardCls} block hover:border-blue-300`}>
            <h2 className="font-semibold">{t.title}</h2>
            <p className="mt-1 text-sm text-gray-600">{t.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
