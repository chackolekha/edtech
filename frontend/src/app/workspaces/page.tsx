"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, cardCls } from "@/components/ui";

interface WS {
  id: string;
  listing_id: string;
  status: string;
  listing_title: string | null;
}

export default function WorkspacesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<WS[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) api.get<WS[]>("/workspaces/mine").then(setItems).catch(setError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  if (loading || !user) return <Loading />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Project workspaces</h1>
      <ErrorBox error={error} />
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty>
          No workspaces yet — they are created when a project team is formed.
        </Empty>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((w) => (
            <Link key={w.id} href={`/workspaces/${w.id}`} className={`${cardCls} block hover:border-blue-300`}>
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">{w.listing_title ?? "Project"}</h2>
                <Badge color={w.status === "completed" ? "green" : w.status === "submitted" ? "yellow" : "blue"}>
                  {w.status}
                </Badge>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
