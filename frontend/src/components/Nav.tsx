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

export default function Nav() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const linkCls = (href: string) =>
    `text-sm ${pathname?.startsWith(href) ? "font-semibold text-blue-700" : "text-gray-600 hover:text-gray-900"}`;

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
        <Link href="/" className="text-lg font-bold text-blue-700">
          EdTech
        </Link>
        {user && (
          <nav className="flex items-center gap-4">
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
              <Link href="/me" className="text-sm text-gray-600 hover:text-gray-900">
                {user.email}
              </Link>
              <button
                onClick={() => {
                  logout();
                  router.push("/");
                }}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
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
                className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
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
