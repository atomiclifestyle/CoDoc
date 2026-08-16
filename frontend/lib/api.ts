import type { DocResponse, RepoSummary, SessionUser } from "@/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * Thin wrapper around fetch that talks to the CoDoc FastAPI backend.
 * Auth is a server-side session cookie set by the backend (Starlette
 * SessionMiddleware) after /auth/login or /auth/demo-login — every call
 * here sends credentials so that cookie rides along.
 *
 * Note: if the frontend and backend are on different origins, the backend
 * must respond with `Access-Control-Allow-Origin: <exact frontend origin>`
 * and `Access-Control-Allow-Credentials: true`, and its session cookie
 * needs `SameSite=None; Secure` for the browser to send it cross-site.
 */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`CoDoc API error ${res.status}: ${body || res.statusText}`);
  }

  return res.json() as Promise<T>;
}

export function fetchCurrentUser() {
  return request<SessionUser>("/auth/me", { method: "GET" });
}

export function logout() {
  return request<{ status: string; message: string }>("/auth/logout", {
    method: "POST",
  });
}

export function demoLogin(email: string, password: string) {
  const params = new URLSearchParams({ email, password });
  return request<{ status: string; message: string }>(
    `/auth/demo-login?${params.toString()}`,
    { method: "POST" }
  );
}

export async function listTrackedRepos(): Promise<RepoSummary[]> {
  const data = await request<{ repos: RepoSummary[] }>("/repo", { method: "GET" });
  return data.repos;
}

export function trackRepo(payload: {
  repo_url: string;
  page_name: string;
  can_update_wiki?: boolean;
}) {
  return request<{ status: string; repo: { repo_url: string; page_name: string } }>(
    "/repo",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export function getLatestDoc(repoUrl: string) {
  const params = new URLSearchParams({ repo_url: repoUrl });
  return request<DocResponse>(`/doc?${params.toString()}`, { method: "GET" });
}
