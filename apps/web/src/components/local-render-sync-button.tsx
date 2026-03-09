"use client";

import { useEffect, useState } from "react";

type SyncResponse = {
  status?: string;
  message?: string;
  error?: string;
  local_items?: number;
  render_items?: number;
  render_items_after?: number;
  total_upserted?: number;
  total_deleted?: number;
  duration_seconds?: number;
};

type LocalRenderSyncButtonProps = {
  variant?: "card" | "nav";
};

export function LocalRenderSyncButton({
  variant = "card",
}: LocalRenderSyncButtonProps) {
  const [isSyncing, setIsSyncing] = useState(false);
  const [isLoadingPreflight, setIsLoadingPreflight] = useState(true);
  const [preflight, setPreflight] = useState<SyncResponse | null>(null);
  const [result, setResult] = useState<SyncResponse | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadPreflight() {
      setIsLoadingPreflight(true);
      try {
        const response = await fetch("/api/admin/sync-render-db", {
          method: "GET",
          cache: "no-store",
        });
        const payload = (await response.json()) as SyncResponse;
        if (!response.ok) {
          throw new Error(payload.error || "Preflight failed.");
        }
        if (isMounted) setPreflight(payload);
      } catch (error) {
        if (isMounted) {
          setPreflight({
            status: "error",
            error:
              error instanceof Error ? error.message : "Preflight failed.",
          });
        }
      } finally {
        if (isMounted) setIsLoadingPreflight(false);
      }
    }

    void loadPreflight();
    return () => {
      isMounted = false;
    };
  }, []);

  async function handleSync(mode: "incremental" | "full") {
    const label =
      mode === "full"
        ? "This will TRUNCATE all Render tables and do a full restore. Continue?"
        : "This will push changed rows to Render. Continue?";
    if (!window.confirm(label)) return;

    setIsSyncing(true);
    setResult(null);
    try {
      const response = await fetch(
        `/api/admin/sync-render-db?mode=${mode}`,
        { method: "POST" },
      );
      const payload = (await response.json()) as SyncResponse;
      if (!response.ok) {
        throw new Error(payload.error || "Sync failed.");
      }
      setResult(payload);
    } catch (error) {
      setResult({
        status: "error",
        error: error instanceof Error ? error.message : "Sync failed.",
      });
    } finally {
      setIsSyncing(false);
    }
  }

  const preflightError = preflight?.status === "error" ? preflight.error : null;
  const isError = result?.status === "error";
  const buttonLabel = isSyncing ? "Syncing..." : "Sync Render DB";
  const isDisabled = isSyncing || isLoadingPreflight || Boolean(preflightError);

  const summaryLine = preflight
    ? `Local: ${preflight.local_items ?? "?"} / Render: ${preflight.render_items ?? "?"}`
    : "";

  function formatResult(r: SyncResponse): string {
    if (r.total_upserted !== undefined) {
      const parts = [`${r.total_upserted} upserted`];
      if (r.total_deleted) parts.push(`${r.total_deleted} deleted`);
      parts.push(`${r.duration_seconds}s`);
      return parts.join(", ");
    }
    return `Render: ${r.render_items_after ?? "?"} items, ${r.duration_seconds}s`;
  }

  if (variant === "nav") {
    return (
      <div className="flex flex-col gap-1">
        <button
          type="button"
          onClick={() => handleSync("incremental")}
          title={preflightError ?? summaryLine}
          disabled={isDisabled}
          className="rounded-md border border-edge px-3 py-1.5 font-ui text-xs text-ink transition-colors hover:border-edge-strong hover:text-accent disabled:cursor-not-allowed disabled:opacity-60"
        >
          {buttonLabel}
        </button>
        {preflightError ? (
          <p className="max-w-56 font-ui text-xs text-danger">
            {preflightError}
          </p>
        ) : result ? (
          <p
            className={`max-w-56 font-ui text-xs ${isError ? "text-danger" : "text-valid"}`}
          >
            {isError ? result.error : formatResult(result)}
          </p>
        ) : (
          <p className="font-ui text-[11px] text-ink-muted">
            {isLoadingPreflight ? "Checking..." : summaryLine}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="mt-6 rounded-lg border border-edge bg-surface-alt p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="small-caps text-caution">Local Admin</p>
          <p className="mt-1 font-ui text-sm text-ink-secondary">
            Push local database changes to hosted Render Postgres.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleSync("incremental")}
            disabled={isDisabled}
            className="rounded-md border border-edge px-4 py-2 font-ui text-sm text-ink transition-colors hover:border-edge-strong hover:text-accent disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSyncing ? "Syncing..." : "Incremental Sync"}
          </button>
          <button
            type="button"
            onClick={() => handleSync("full")}
            disabled={isDisabled}
            className="rounded-md border border-edge px-4 py-2 font-ui text-sm text-ink-muted transition-colors hover:border-edge-strong hover:text-caution disabled:cursor-not-allowed disabled:opacity-60"
          >
            Full Sync
          </button>
        </div>
      </div>
      <div className="mt-3 font-ui text-sm text-ink-secondary">
        {isLoadingPreflight ? (
          <p>Checking Render DB...</p>
        ) : preflightError ? (
          <p className="text-danger">{preflightError}</p>
        ) : (
          <p>
            Local items:{" "}
            <span className="font-data text-ink">
              {preflight?.local_items ?? "?"}
            </span>{" "}
            / Render items:{" "}
            <span className="font-data text-ink">
              {preflight?.render_items ?? "?"}
            </span>
          </p>
        )}
      </div>
      {result && (
        <p
          className={`mt-3 font-ui text-sm ${isError ? "text-danger" : "text-valid"}`}
        >
          {isError ? result.error : `${result.message} ${formatResult(result)}`}
        </p>
      )}
    </div>
  );
}
