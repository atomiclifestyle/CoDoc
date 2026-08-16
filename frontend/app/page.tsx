"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSessionUser } from "@/lib/useSession";
import GoogleSignInButton from "@/components/GoogleSignInButton";
import TryDemoButton from "@/components/TryDemoButton";
import FullPageLoader from "@/components/FullPageLoader";

export default function LoginPage() {
  const router = useRouter();
  const { user, loading } = useSessionUser();

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [loading, user, router]);

  if (loading || user) {
    return <FullPageLoader />;
  }

  return (
    <main className="grid min-h-screen grid-cols-1 md:grid-cols-2">
      {/* Left: sign-in */}
      <section className="flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm">
          <div className="mb-10 flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-sm bg-ink text-[11px] font-mono font-semibold text-paper">
              C
            </span>
            <span className="font-mono text-sm tracking-wide text-muted">
              CoDoc
            </span>
          </div>

          <h1 className="text-2xl font-semibold leading-snug text-ink">
            Documentation that keeps up with your repo.
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Sign in to track a repository and CoDoc will generate and
            maintain its docs automatically, on every change.
          </p>

          <div className="mt-8">
            <GoogleSignInButton />
          </div>

          <div className="my-5 flex items-center gap-3">
            <span className="h-px flex-1 bg-line" />
            <span className="font-mono text-[11px] uppercase tracking-wide text-muted/70">
              or
            </span>
            <span className="h-px flex-1 bg-line" />
          </div>

          <TryDemoButton />

          <p className="mt-6 text-xs leading-relaxed text-muted">
            CoDoc only reads repository metadata needed to generate
            documentation. By continuing you agree to sign in with your
            Google account.
          </p>
        </div>
      </section>

      {/* Right: signature terminal panel */}
      <section className="hidden items-center justify-center bg-ink px-10 py-16 md:flex">
        <div className="w-full max-w-md">
          <div className="overflow-hidden rounded-md border border-white/10 bg-[#1c1d22] shadow-2xl">
            <div className="flex items-center gap-1.5 border-b border-white/10 px-4 py-3">
              <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
              <span className="h-2.5 w-2.5 rounded-full bg-white/20" />
              <span className="ml-3 font-mono text-[11px] text-white/40">
                codoc — generating
              </span>
            </div>
            <div className="space-y-2 px-5 py-6 font-mono text-[12.5px] leading-relaxed">
              <p className="text-white/40">$ codoc track github.com/acme/api</p>
              <p className="text-emerald-400">✓ cloned acme/api @ main</p>
              <p className="text-emerald-400">✓ parsed 48 modules, 212 symbols</p>
              <p className="text-white/40">→ writing docs/generated/README.md</p>
              <p className="text-white/70">
                # API Reference<br />
                Auto-generated from source. Last synced just now.
              </p>
              <p className="mt-3 flex items-center gap-2 text-white/40">
                <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-emerald-400" />
                watching for new commits
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
