"use client";

import { useEffect, useState } from "react";
import { fetchCurrentUser } from "@/lib/api";
import type { SessionUser } from "@/types";

/**
 * Client-side session check. This MUST run in the browser: the backend's
 * session cookie lives on the backend's own origin, so only a request made
 * directly by the browser to that origin (with credentials: "include")
 * will actually carry it. A Next.js server component has no way to see
 * that cookie — it was never sent to the frontend's origin in the first
 * place — so don't try to check auth server-side here.
 */
export function useSessionUser() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    fetchCurrentUser()
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch(() => {
        if (!cancelled) setUser(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { user, loading };
}
