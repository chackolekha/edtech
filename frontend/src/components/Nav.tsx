"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

const links = [
  { href: "/communities", label: "Communities" },
  { href: "/listings", label: "Projects" },
  { href: "/mentors", label: "Mentors" },
  { href: "/trainings", label: "Trainings" },
];

const ROLE_LABELS: Record<string, string> = {
  student: "Student",
  mentor: "Mentor",
  provider: "Provider",
  admin: "Admin",
};

export default function Nav() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const linkCls = (href: string) =>
    `rounded-md px-2.5 py-1.5 text-sm transition ${
      pathname?.startsWith(href)
        ? "bg-accent-soft font-semibold text-accent-strong"
        : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
    }`;

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-5 px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent text-sm font-bold text-white">
            E
          </span>
          <span className="text-lg font-bold tracking-tight text-gray-900">EdTech</span>
        </Link>
        {user && (
          <nav className="flex items-center gap-1">
            {links.map((l) => (
              <Link key={l.href} href={l.href} className={linkCls(l.href)}>
                {l.label}
              </Link>
            ))}
            <Link href="/workspaces" className={linkCls("/workspaces")}>
              Workspaces
            </Link>
            {user.role === "student" && (
              <Link href="/applications" className={linkCls("/applications")}>
                Applications
              </Link>
            )}
            <Link href="/portfolio" className={linkCls("/portfolio")}>
              Portfolio
            </Link>
            {(user.role === "mentor" || user.role === "student") && (
              <Link href="/mentorship" className={linkCls("/mentorship")}>
                Mentorship
              </Link>
            )}
            {user.role === "admin" && (
              <Link href="/admin" className={linkCls("/admin")}>
                Admin
              </Link>
            )}
          </nav>
        )}
        <div className="ml-auto flex items-center gap-3">
          {user ? (
            <>
              <Link href="/notifications" className={linkCls("/notifications")}>
                Notifications
              </Link>
              <span className="rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-semibold text-accent-strong ring-1 ring-inset ring-accent-muted">
                {ROLE_LABELS[user.role] ?? user.role}
              </span>
              <Link href="/me" className="max-w-40 truncate text-sm text-gray-600 hover:text-gray-900">
                {user.email}
              </Link>
              <button
                onClick={() => {
                  logout();
                  router.push("/");
                }}
                className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 transition hover:bg-gray-50"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">
                Log in
              </Link>
              <Link
                href="/register"
                className="rounded-lg bg-accent px-3.5 py-1.5 text-sm font-medium text-white shadow-xs transition hover:bg-accent-strong"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
