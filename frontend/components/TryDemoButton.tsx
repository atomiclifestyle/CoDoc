"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { demoLogin } from "@/lib/api";

// The backend checks these against its own DEMO_EMAIL / DEMO_PASSWORD env
// vars — set matching values here via NEXT_PUBLIC_DEMO_EMAIL /
// NEXT_PUBLIC_DEMO_PASSWORD so the button can complete the same call a real
// demo user would make.
const DEMO_EMAIL = process.env.NEXT_PUBLIC_DEMO_EMAIL ?? "";
const DEMO_PASSWORD = process.env.NEXT_PUBLIC_DEMO_PASSWORD ?? "";

export default function TryDemoButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);
    try {
      await demoLogin(DEMO_EMAIL, DEMO_PASSWORD);
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Demo login is unavailable right now."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={loading}
        className="flex w-full items-center justify-center gap-2 rounded-sm border border-dashed border-line bg-transparent px-5 py-3 text-sm font-medium text-muted transition-colors hover:border-ink/30 hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal disabled:opacity-50"
      >
        <span className="font-mono text-xs">→</span>
        {loading ? "Signing in…" : "Try Demo"}
      </button>
      {error && <p className="mt-2 text-xs text-danger">{error}</p>}
    </div>
  );
}
