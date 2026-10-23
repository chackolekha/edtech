"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { ErrorBox, Field, btnCls, cardCls, inputCls } from "@/components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me = await login(email, password);
      router.push(me.onboarding_complete ? "/" : "/onboarding");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm py-10">
      <div className={cardCls}>
        <h1 className="text-xl font-bold">Log in</h1>
        <form onSubmit={submit} className="mt-4 space-y-4">
          <Field label="Email">
            <input className={inputCls} type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)} />
          </Field>
          <Field label="Password">
            <input className={inputCls} type="password" required value={password}
              onChange={(e) => setPassword(e.target.value)} />
          </Field>
          <ErrorBox error={error} />
          <button className={btnCls} disabled={busy}>
            {busy ? "Logging in…" : "Log in"}
          </button>
        </form>
        <div className="mt-4 flex justify-between text-sm">
          <Link href="/forgot-password" className="text-accent hover:underline">
            Forgot password?
          </Link>
          <Link href="/register" className="text-accent hover:underline">
            Create account
          </Link>
        </div>
      </div>
    </div>
  );
}
