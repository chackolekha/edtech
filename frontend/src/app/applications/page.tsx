"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Badge, Empty, ErrorBox, Loading, btnDanger, cardCls } from "@/components/ui";

interface Application {
  id: string;
  listing_id: string;
  cover_note: string | null;
  status: string;
  created_at: string;
}

export default function ApplicationsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Application[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  async function load() {
    setItems(await api.get<Application[]>("/applications/mine"));
  }

  useEffect(() => {
    if (!loading && !user) router.push("/login");
    if (user) load().catch(setError);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, user]);

  if (loading || !user) return <Loading />;

  async function withdraw(id: string) {
    try {
      await api.post(`/applications/${id}/withdraw`);
      await load();
    } catch (e) {
      setError(e);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-bold">My applications</h1>
      <ErrorBox error={error} />
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <Empty>
          No applications yet.{" "}
          <Link href="/listings" className="text-blue-600 underline">Browse projects →</Link>
        </Empty>
      ) : (
        items.map((a) => (
          <div key={a.id} className={cardCls}>
            <div className="flex items-center justify-between">
              <Link href={`/listings/${a.listing_id}`} className="font-medium text-blue-700 hover:underline">
                View listing
              </Link>
              <Badge color={
                a.status === "accepted" ? "green" :
                a.status === "rejected" ? "red" :
                a.status === "withdrawn" ? "yellow" : "gray"
              }>{a.status}</Badge>
            </div>
            {a.cover_note && <p className="mt-1 text-sm text-gray-600">{a.cover_note}</p>}
            <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
              <span>{new Date(a.created_at).toLocaleDateString()}</span>
              {a.status === "submitted" && (
                <button onClick={() => withdraw(a.id)} className={btnDanger}>Withdraw</button>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
