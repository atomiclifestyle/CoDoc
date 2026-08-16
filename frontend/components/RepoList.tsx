"use client";

import type { RepoSummary } from "@/types";

interface RepoListProps {
  repos: RepoSummary[];
  selectedRepoUrl: string | null;
  onSelect: (repo: RepoSummary) => void;
  loading: boolean;
}

export default function RepoList({ repos, selectedRepoUrl, onSelect, loading }: RepoListProps) {
  if (loading) {
    return (
      <ul className="space-y-2">
        {[0, 1, 2].map((i) => (
          <li key={i} className="h-14 animate-pulse rounded-sm bg-line/40" />
        ))}
      </ul>
    );
  }

  if (repos.length === 0) {
    return (
      <div className="rounded-sm border border-dashed border-line px-4 py-8 text-center">
        <p className="text-sm text-muted">No repositories tracked yet.</p>
        <p className="mt-1 text-xs text-muted/70">
          Add one above and CoDoc will start generating docs.
        </p>
      </div>
    );
  }

  return (
    <ul className="space-y-1.5">
      {repos.map((repo) => {
        const isSelected = repo.repo_url === selectedRepoUrl;
        return (
          <li key={repo.repo_url}>
            <button
              onClick={() => onSelect(repo)}
              className={`flex w-full items-center justify-between gap-3 rounded-sm border px-3.5 py-3 text-left transition-colors ${
                isSelected
                  ? "border-ink/30 bg-signal-soft"
                  : "border-line bg-surface hover:border-ink/20"
              }`}
            >
              <div className="min-w-0">
                <p className="truncate font-mono text-sm text-ink">{repo.page_name}</p>
                <p className="mt-0.5 truncate text-xs text-muted">{repo.repo_url}</p>
              </div>
              {repo.can_update_wiki && (
                <span className="shrink-0 rounded-full bg-signal-soft px-2 py-0.5 font-mono text-[10px] text-signal">
                  wiki
                </span>
              )}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
