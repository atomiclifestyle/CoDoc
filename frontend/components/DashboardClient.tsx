"use client";

import { useCallback, useEffect, useState } from "react";
import { getLatestDoc, listTrackedRepos, trackRepo } from "@/lib/api";
import type { DocResponse, RepoSummary } from "@/types";
import TrackRepoForm from "@/components/TrackRepoForm";
import RepoList from "@/components/RepoList";
import DocViewer from "@/components/DocViewer";
import SignOutButton from "@/components/SignOutButton";

interface DashboardClientProps {
  userName: string;
  userEmail: string;
  isDemo: boolean;
}

export default function DashboardClient({ userName, userEmail, isDemo }: DashboardClientProps) {
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [reposLoading, setReposLoading] = useState(true);
  const [reposError, setReposError] = useState<string | null>(null);

  const [selectedRepo, setSelectedRepo] = useState<RepoSummary | null>(null);
  const [doc, setDoc] = useState<DocResponse | null>(null);
  const [docLoading, setDocLoading] = useState(false);
  const [docError, setDocError] = useState<string | null>(null);

  const refreshRepos = useCallback(async () => {
    setReposLoading(true);
    setReposError(null);
    try {
      const data = await listTrackedRepos();
      setRepos(data);
    } catch (err) {
      setReposError(err instanceof Error ? err.message : "Failed to load repos.");
    } finally {
      setReposLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshRepos();
  }, [refreshRepos]);

  async function handleTrack(repoUrl: string, pageName: string, canUpdateWiki: boolean) {
    const { repo } = await trackRepo({
      repo_url: repoUrl,
      page_name: pageName,
      can_update_wiki: canUpdateWiki,
    });
    setRepos((prev) => [
      { repo_url: repo.repo_url, page_name: repo.page_name, can_update_wiki: canUpdateWiki },
      ...prev.filter((r) => r.repo_url !== repo.repo_url),
    ]);
  }

  async function handleSelectRepo(repo: RepoSummary) {
    setSelectedRepo(repo);
    setDoc(null);
    setDocError(null);
    setDocLoading(true);
    try {
      const latest = await getLatestDoc(repo.repo_url);
      setDoc(latest);
    } catch (err) {
      setDocError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setDocLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-paper">
      <header className="border-b border-line px-6 py-4 md:px-10">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-sm bg-ink text-[11px] font-mono font-semibold text-paper">
              C
            </span>
            <span className="font-mono text-sm tracking-wide text-muted">CoDoc</span>
          </div>
          <div className="flex items-center gap-3">
            {isDemo && (
              <span className="rounded-full bg-signal-soft px-2.5 py-1 font-mono text-[11px] text-signal">
                Demo account
              </span>
            )}
            <span className="hidden text-sm text-muted sm:inline">
              {userName} · {userEmail}
            </span>
            <SignOutButton />
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-10 md:px-10">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[340px_1fr]">
          {/* Left: track form + repo list */}
          <div className="space-y-8">
            <div className="rounded-md border border-line bg-surface p-5">
              <TrackRepoForm onTrack={handleTrack} />
            </div>

            <div>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-xs font-medium uppercase tracking-wide text-muted">
                  Tracked repositories
                </h2>
                <span className="font-mono text-xs text-muted">{repos.length}</span>
              </div>
              {reposError ? (
                <p className="text-sm text-danger">{reposError}</p>
              ) : (
                <RepoList
                  repos={repos}
                  selectedRepoUrl={selectedRepo?.repo_url ?? null}
                  onSelect={handleSelectRepo}
                  loading={reposLoading}
                />
              )}
            </div>
          </div>

          {/* Right: doc viewer */}
          <div>
            <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-muted">
              Latest generated doc
            </h2>
            <DocViewer repo={selectedRepo} doc={doc} loading={docLoading} error={docError} />
          </div>
        </div>
      </div>
    </main>
  );
}
