"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ErrorBox, Loading, btnCls, cardCls, inputCls } from "@/components/ui";

function VerifyInner() {
  const params = useSearchParams();
  const preset = params.get("token") ?? "";
  const [token, setToken] = useState(preset);
  const [status, setStatus] = useState<"idle" | "busy" | "ok" | "err">("idle");
  const [error, setError] = useState<unknown>(null);

  async function verify(t: string) {
    setStatus("busy");
    setError(null);
    try {
      await api.post("/auth/verify-email", { token: t });
      setStatus("ok");
    } catch (err) {
      setError(err);
      setStatus("err");
    }
  }

  useEffect(() => {
    if (preset) verify(preset);
  }, [preset]);

  return (
    <div className="mx-auto max-w-md py-10">
      <div className={cardCls}>
        <h1 className="text-xl font-bold">Verify email</h1>
        {status === "busy" && <Loading label="Verifying…" />}
        {status === "ok" && (
          <p className="mt-3 text-sm text-green-700">
            Email verified. <Link href="/login" className="text-accent underline">Log in →</Link>
          </p>
        )}
        {status !== "busy" && status !== "ok" && (
          <div className="mt-4 space-y-3">
            <ErrorBox error={error} />
            <input className={inputCls} placeholder="Paste verification token"
              value={token} onChange={(e) => setToken(e.target.value)} />
            <button className={btnCls} onClick={() => verify(token)} disabled={!token}>
              Verify
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<Loading />}>
      <VerifyInner />
    </Suspense>
  );
}
