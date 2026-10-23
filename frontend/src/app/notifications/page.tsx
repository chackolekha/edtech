"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Empty, ErrorBox, Loading, btnSecondary, cardCls } from "@/components/ui";

interface Notif {
  id: string;
  type: string;
  payload: Record<string, string>;
  read_at: string | null;
  created_at: string;
}

const LINKS: Record<string, (p: Record<string, string>) => string> = {
  application_received: (p) => `/listings/${p.listing_id}`,
  application_accepted: (p) => `/listings/${p.listing_id}`,
  application_rejected: () => `/applications`,
  team_formed: (p) => `/workspaces/${p.workspace_id}`,
  workspace_completed: (p) => `/workspaces/${p.workspace_id}`,
  feedback_received: (p) => `/workspaces/${p.workspace_id}`,
  mentor_request: () => `/mentorship`,
  mentor_request_accepted: () => `/mentorship`,
  mentor_request_declined: () => `/mentorship`,
  verification_verified: () => `/`,
  verification_rejected: () => `/`,
  training_completed: (p) => `/trainings/${p.training_id}`,
};

const LABELS: Record<string, string> = {
  application_received: "New application on your listing",
  application_accepted: "Your application was accepted",
  application_rejected: "Your application was rejected",
  team_formed: "You were added to a project team",
  workspace_completed: "A project workspace was completed",
  feedback_received: "New feedback on your workspace",
  mentor_request: "New mentorship request",
  mentor_request_accepted: "Mentorship request accepted",
  mentor_request_declined: "Mentorship request declined",
  verification_verified: "Your account was verified",
  verification_rejected: "Your verification was rejected",
  training_completed: "Training completed",
};

export default function NotificationsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Notif[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  async function load() {
    setItems(await api.get<Notif[]>("/notifications"));
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load().catch(setError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  if (loading || !user) return <Loading />;

  async function markRead(n: Notif) {
    if (!n.read_at) await api.post(`/notifications/${n.id}/read`);
    const href = LINKS[n.type]?.(n.payload);
    if (href) router.push(href);
    else await load();
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Notifications</h1>
        <button className={btnSecondary}
          onClick={async () => { await api.post("/notifications/read-all"); await load(); }}>
          Mark all read
        </button>
      </div>
      <ErrorBox error={error} />
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty>No notifications.</Empty>
      ) : (
        items.map((n) => (
          <button key={n.id} onClick={() => markRead(n)}
            className={`${cardCls} block w-full text-left ${n.read_at ? "opacity-60" : "border-l-4 border-l-accent"}`}>
            <p className="text-sm font-medium">{LABELS[n.type] ?? n.type}</p>
            <p className="mt-0.5 text-xs text-gray-500">
              {new Date(n.created_at).toLocaleString()}
            </p>
          </button>
        ))
      )}
    </div>
  );
}
