"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnCls, btnDanger, btnSecondary, cardCls } from "@/components/ui";

interface Pending {
  id: string;
  email: string;
  role: string;
  display_name: string | null;
  created_at: string;
}

interface Flag {
  id: string;
  target_type: string;
  target_id: string;
  reason: string;
  status: string;
  created_at: string;
}

interface Analytics {
  users_total: number;
  users_by_role: Record<string, number>;
  pending_verifications: number;
  communities: number;
  listings_open: number;
  applications_submitted: number;
  workspaces_active: number;
  workspaces_completed: number;
  trainings: number;
  enrollments: number;
  open_flags: number;
}

type Tab = "verifications" | "flags" | "analytics";

export default function AdminPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("verifications");
  const [pending, setPending] = useState<Pending[] | null>(null);
  const [flags, setFlags] = useState<Flag[] | null>(null);
  const [stats, setStats] = useState<Analytics | null>(null);
  const [error, setError] = useState<unknown>(null);

  async function load() {
    try {
      const [p, f, s] = await Promise.all([
        api.get<Pending[]>("/admin/pending-verifications"),
        api.get<Flag[]>("/admin/flags"),
        api.get<Analytics>("/admin/analytics/summary"),
      ]);
      setPending(p);
      setFlags(f);
      setStats(s);
    } catch (e) {
      setError(e);
    }
  }

  useEffect(() => {
    if (!loading && (!user || user.role !== "admin")) router.push("/");
    if (user?.role === "admin") load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  if (loading || !user || user.role !== "admin") return <Loading />;

  async function verify(id: string, action: "verify" | "reject") {
    await api.post(`/admin/users/${id}/${action}`);
    await load();
  }

  async function flagAction(id: string, action: "resolve" | "dismiss") {
    await api.post(`/admin/flags/${id}/${action}`);
    await load();
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Admin console</h1>
      <div className="flex gap-2">
        {(["verifications", "flags", "analytics"] as Tab[]).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={tab === t ? btnCls : btnSecondary}>
            {t}
            {t === "verifications" && pending ? ` (${pending.length})` : ""}
            {t === "flags" && flags ? ` (${flags.length})` : ""}
          </button>
        ))}
      </div>
      <ErrorBox error={error} />

      {tab === "verifications" && (
        pending === null ? <Loading /> : pending.length === 0 ? (
          <Empty>No pending verifications.</Empty>
        ) : (
          pending.map((u) => (
            <div key={u.id} className={`${cardCls} flex items-center justify-between`}>
              <div>
                <p className="font-medium">{u.display_name ?? u.email}</p>
                <p className="text-sm text-gray-500">{u.email} · <Badge>{u.role}</Badge></p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => verify(u.id, "verify")} className={btnCls}>Verify</button>
                <button onClick={() => verify(u.id, "reject")} className={btnDanger}>Reject</button>
              </div>
            </div>
          ))
        )
      )}

      {tab === "flags" && (
        flags === null ? <Loading /> : flags.length === 0 ? (
          <Empty>No open flags.</Empty>
        ) : (
          flags.map((f) => (
            <div key={f.id} className={`${cardCls} flex items-center justify-between`}>
              <div>
                <p className="text-sm"><Badge color="red">{f.target_type}</Badge> {f.reason}</p>
                <p className="mt-1 text-xs text-gray-500">
                  {f.target_id} · {new Date(f.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => flagAction(f.id, "resolve")} className={btnCls}>Resolve</button>
                <button onClick={() => flagAction(f.id, "dismiss")} className={btnSecondary}>Dismiss</button>
              </div>
            </div>
          ))
        )
      )}

      {tab === "analytics" && (
        stats === null ? <Loading /> : (
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              ["Total users", stats.users_total],
              ["Pending verifications", stats.pending_verifications],
              ["Communities", stats.communities],
              ["Open listings", stats.listings_open],
              ["Applications", stats.applications_submitted],
              ["Active workspaces", stats.workspaces_active],
              ["Completed workspaces", stats.workspaces_completed],
              ["Trainings", stats.trainings],
              ["Enrollments", stats.enrollments],
              ["Open flags", stats.open_flags],
            ].map(([label, value]) => (
              <div key={label as string} className={cardCls}>
                <p className="text-2xl font-bold">{value}</p>
                <p className="text-sm text-gray-500">{label}</p>
              </div>
            ))}
            <div className={`${cardCls} sm:col-span-3`}>
              <p className="text-sm font-medium text-gray-700">Users by role</p>
              <div className="mt-2 flex gap-3">
                {Object.entries(stats.users_by_role).map(([role, count]) => (
                  <Badge key={role} color="blue">{role}: {count}</Badge>
                ))}
              </div>
            </div>
          </div>
        )
      )}
    </div>
  );
}
