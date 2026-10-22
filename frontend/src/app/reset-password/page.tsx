"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { api } from "@/lib/api";
import { ErrorBox, Field, Loading, btnCls, cardCls, inputCls } from "@/components/ui";

function ResetInner() {
  const params = useSearchParams();
  const [token, setToken] = useState(params.get("token") ?? "");
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.post("/auth/password-reset/confirm", {
        token,
        new_password: password,
      });
      setDone(true);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm py-10">
      <div className={cardCls}>
        <h1 className="text-xl font-bold">Choose a new password</h1>
        {done ? (
          <p className="mt-3 text-sm text-green-700">
            Password updated.{" "}
            <Link href="/login" className="text-blue-600 underline">Log in →</Link>
          </p>
        ) : (
          <form onSubmit={submit} className="mt-4 space-y-4">
            <Field label="Reset token">
              <input className={inputCls} required value={token}
                onChange={(e) => setToken(e.target.value)} />
            </Field>
            <Field label="New password (min 8 chars)">
              <input className={inputCls} type="password" required minLength={8}
                value={password} onChange={(e) => setPassword(e.target.value)} />
            </Field>
            <ErrorBox error={error} />
            <button className={btnCls} disabled={busy}>
              {busy ? "Saving…" : "Set password"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<Loading />}>
      <ResetInner />
    </Suspense>
  );
}
