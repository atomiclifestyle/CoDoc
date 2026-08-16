"use client";

import { useState, type FormEvent } from "react";

interface TrackRepoFormProps {
  onTrack: (repoUrl: string, pageName: string, canUpdateWiki: boolean) => Promise<void>;
}

/** Derives a reasonable default page name ("acme/api" -> "api") from a repo URL. */
function suggestPageName(repoUrl: string): string {
  const cleaned = repoUrl.trim().replace(/\.git$/, "").replace(/\/+$/, "");
  const segments = cleaned.split("/");
  return segments[segments.length - 1] || "";
}

export default function TrackRepoForm({ onTrack }: TrackRepoFormProps) {
  const [repoUrl, setRepoUrl] = useState("");
  const [pageName, setPageName] = useState("");
  const [pageNameTouched, setPageNameTouched] = useState(false);
  const [canUpdateWiki, setCanUpdateWiki] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleRepoUrlChange(value: string) {
    setRepoUrl(value);
    if (!pageNameTouched) {
      setPageName(suggestPageName(value));
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmedUrl = repoUrl.trim();
    const trimmedPage = pageName.trim();
    if (!trimmedUrl || !trimmedPage) return;

    setSubmitting(true);
    setError(null);
    try {
      await onTrack(trimmedUrl, trimmedPage, canUpdateWiki);
      setRepoUrl("");
      setPageName("");
      setPageNameTouched(false);
      setCanUpdateWiki(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not track that repo.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label
          htmlFor="repo-url"
          className="mb-2 block text-xs font-medium uppercase tracking-wide text-muted"
        >
          Track a repository
        </label>
        <div className="flex items-stretch overflow-hidden rounded-sm border border-line bg-surface focus-within:border-ink/40">
          <span className="flex items-center border-r border-line bg-[#f5f5f3] px-3 font-mono text-sm text-muted">
            $
          </span>
          <input
            id="repo-url"
            type="text"
            inputMode="url"
            placeholder="github.com/org/repo"
            value={repoUrl}
            onChange={(e) => handleRepoUrlChange(e.target.value)}
            className="flex-1 bg-transparent px-3 py-2.5 font-mono text-sm text-ink placeholder:text-muted/60 focus:outline-none"
          />
        </div>
      </div>

      <div>
        <label
          htmlFor="page-name"
          className="mb-2 block text-xs font-medium uppercase tracking-wide text-muted"
        >
          Page name
        </label>
        <input
          id="page-name"
          type="text"
          placeholder="api"
          value={pageName}
          onChange={(e) => {
            setPageName(e.target.value);
            setPageNameTouched(true);
          }}
          className="w-full rounded-sm border border-line bg-surface px-3 py-2.5 font-mono text-sm text-ink placeholder:text-muted/60 focus:border-ink/40 focus:outline-none"
        />
      </div>

      <label className="flex items-center gap-2 text-xs text-muted">
        <input
          type="checkbox"
          checked={canUpdateWiki}
          onChange={(e) => setCanUpdateWiki(e.target.checked)}
          className="h-3.5 w-3.5 rounded-sm border-line accent-signal"
        />
        Also publish updates to the GitHub wiki
      </label>

      <button
        type="submit"
        disabled={submitting || !repoUrl.trim() || !pageName.trim()}
        className="w-full rounded-sm bg-ink px-4 py-2.5 text-sm font-medium text-paper transition-opacity hover:opacity-90 disabled:opacity-40"
      >
        {submitting ? "Tracking…" : "Track"}
      </button>

      {error && <p className="text-xs text-danger">{error}</p>}
    </form>
  );
}
