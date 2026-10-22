"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { ErrorBox, Field, btnCls, cardCls, inputCls } from "@/components/ui";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [devToken, setDevToken] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api.post<{ dev_reset_token: string | null }>(
        "/auth/password-reset",
        { email },
      );
      setDevToken(res.dev_reset_token);
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
        <h1 className="text-xl font-bold">Reset password</h1>
        {done ? (
          <div className="mt-3 text-sm text-gray-600">
            <p>If that email exists, a reset link was sent.</p>
            {devToken && (
              <div className="mt-3 rounded-md bg-yellow-50 p-3 text-yellow-900">
                <b>Dev mode:</b>{" "}
                <Link href={`/reset-password?token=${encodeURIComponent(devToken)}`}
                  className="text-blue-700 underline">
                  Reset now →
                </Link>
              </div>
            )}
          </div>
        ) : (
          <form onSubmit={submit} className="mt-4 space-y-4">
            <Field label="Email">
              <input className={inputCls} type="email" required value={email}
                onChange={(e) => setEmail(e.target.value)} />
            </Field>
            <ErrorBox error={error} />
            <button className={btnCls} disabled={busy}>
              {busy ? "Sending…" : "Send reset link"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
