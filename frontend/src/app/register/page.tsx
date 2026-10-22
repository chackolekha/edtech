"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { ErrorBox, Field, btnCls, cardCls, inputCls } from "@/components/ui";

const roles = [
  { value: "student", label: "Student" },
  { value: "mentor", label: "Mentor" },
  { value: "provider", label: "Organisation / Provider" },
];

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await api.post<{ dev_verify_token: string | null }>(
        "/auth/register",
        { email, password, role },
      );
      setDevToken(res.dev_verify_token);
      setDone(true);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="mx-auto max-w-md py-10">
        <div className={cardCls}>
          <h1 className="text-xl font-bold">Check your email</h1>
          <p className="mt-2 text-sm text-gray-600">
            We sent a verification link to <b>{email}</b>.
          </p>
          {devToken && (
            <div className="mt-4 rounded-md bg-yellow-50 p-3 text-sm text-yellow-900">
              <b>Dev mode:</b> no real email is sent. Verify directly:
              <Link
                href={`/verify-email?token=${encodeURIComponent(devToken)}&email=${encodeURIComponent(email)}`}
                className="mt-2 block break-all text-blue-700 underline"
              >
                Verify email →
              </Link>
            </div>
          )}
          <Link href="/login" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
            Go to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-sm py-10">
      <div className={cardCls}>
        <h1 className="text-xl font-bold">Create account</h1>
        <form onSubmit={submit} className="mt-4 space-y-4">
          <Field label="I am a…">
            <select className={inputCls} value={role} onChange={(e) => setRole(e.target.value)}>
              {roles.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </Field>
          {(role === "mentor" || role === "provider") && (
            <p className="text-xs text-gray-500">
              Mentor and provider accounts are reviewed by an admin before they
              can post or respond.
            </p>
          )}
          <Field label="Email">
            <input className={inputCls} type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)} />
          </Field>
          <Field label="Password (min 8 chars)">
            <input className={inputCls} type="password" required minLength={8}
              value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
          <ErrorBox error={error} />
          <button className={btnCls} disabled={busy}>
            {busy ? "Creating…" : "Sign up"}
          </button>
        </form>
        <p className="mt-4 text-sm">
          <Link href="/login" className="text-blue-600 hover:underline">
            Already have an account? Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
