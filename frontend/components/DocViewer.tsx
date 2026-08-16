"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { DocResponse, RepoSummary } from "@/types";

interface DocViewerProps {
  repo: RepoSummary | null;
  doc: DocResponse | null;
  loading: boolean;
  error: string | null;
}

export default function DocViewer({ repo, doc, loading, error }: DocViewerProps) {
  if (!repo) {
    return (
      <div className="flex h-full min-h-[420px] flex-col items-center justify-center rounded-md border border-dashed border-line px-6 text-center">
        <p className="text-sm text-muted">Select a tracked repository</p>
        <p className="mt-1 text-xs text-muted/70">
          Its latest generated doc will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-line bg-surface">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-4">
        <div>
          <p className="font-mono text-sm text-ink">{repo.page_name}</p>
          <p className="mt-0.5 font-mono text-xs text-muted">
            {doc?.updated_at
              ? `updated ${new Date(doc.updated_at).toLocaleString()}`
              : "not generated yet"}
          </p>
        </div>
        <a
          href={`https://github.com/${repo.repo_url}`}
          target="_blank"
          rel="noreferrer"
          className="text-xs font-medium text-signal hover:underline"
        >
          View repo ↗
        </a>
      </div>

      <div className="px-6 py-6">
        {loading && (
          <div className="space-y-3">
            <div className="h-4 w-1/3 animate-pulse rounded bg-line/50" />
            <div className="h-3 w-full animate-pulse rounded bg-line/40" />
            <div className="h-3 w-5/6 animate-pulse rounded bg-line/40" />
            <div className="h-3 w-2/3 animate-pulse rounded bg-line/40" />
          </div>
        )}

        {!loading && error && (
          <div className="rounded-sm border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
            Couldn&apos;t load the latest doc. {error}
          </div>
        )}

        {!loading && !error && doc && !doc.content && (
          <p className="text-sm text-muted">
            No doc has been generated for this repo yet — it will appear here
            once CoDoc finishes its first run.
          </p>
        )}

        {!loading && !error && doc?.content && (
          <div className="doc-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{doc.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
