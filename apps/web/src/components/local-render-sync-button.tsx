"use client";

import { useEffect, useState } from "react";

type SyncResponse = {
  status?: string;
  message?: string;
  error?: string;
  duration_seconds?: number;
  source_summary?: {
    toolkit_item_count?: number;
    first_pass_distinct_slug_count?: number;
  };
  target_summary?: {
    toolkit_item_count?: number;
    first_pass_distinct_slug_count?: number;
  };
  target_after_summary?: {
    toolkit_item_count?: number;
    first_pass_distinct_slug_count?: number;
  };
  render_database_source?: string;
  render_database?: {
    postgres_id?: string | null;
    postgres_name?: string | null;
    display_url?: string | null;
  };
};

export function LocalRenderSyncButton() {
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
          throw new Error(payload.error || "Render DB sync preflight failed.");
        }
        if (isMounted) {
          setPreflight(payload);
        }
      } catch (error) {
        if (isMounted) {
          setPreflight({
            status: "error",
            error:
              error instanceof Error
                ? error.message
                : "Render DB sync preflight failed.",
          });
        }
      } finally {
        if (isMounted) {
          setIsLoadingPreflight(false);
        }
      }
    }

    void loadPreflight();
    return () => {
      isMounted = false;
    };
  }, []);

  async function handleClick() {
    const confirmed = window.confirm(
      "This will overwrite the hosted Render Postgres database with your local database. Continue?",
    );
    if (!confirmed) {
      return;
    }

    setIsSyncing(true);
    setResult(null);
    try {
      const response = await fetch("/api/admin/sync-render-db", {
        method: "POST",
      });
      const payload = (await response.json()) as SyncResponse;
      if (!response.ok) {
        throw new Error(payload.error || "Render DB sync failed.");
      }
      setResult(payload);
    } catch (error) {
      setResult({
        status: "error",
        error: error instanceof Error ? error.message : "Render DB sync failed.",
      });
    } finally {
      setIsSyncing(false);
    }
  }

  const preflightError = preflight?.status === "error" ? preflight.error : null;
  const isError = result?.status === "error";

  return (
    <div className="mt-6 rounded-lg border border-edge bg-surface-alt p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="small-caps text-caution">Local Admin</p>
          <p className="mt-1 font-ui text-sm text-ink-secondary">
            Overwrite the hosted Render Postgres database with the current local
            database.
          </p>
        </div>
        <button
          type="button"
          onClick={handleClick}
          disabled={isSyncing || isLoadingPreflight || Boolean(preflightError)}
          className="rounded-md border border-edge px-4 py-2 font-ui text-sm text-ink transition-colors hover:border-edge-strong hover:text-accent disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSyncing ? "Syncing Render DB..." : "Sync Render DB"}
        </button>
      </div>
      <div className="mt-3 font-ui text-sm text-ink-secondary">
        {isLoadingPreflight ? (
          <p>Checking Render DB target...</p>
        ) : preflightError ? (
          <p className="text-danger">{preflightError}</p>
        ) : (
          <>
            <p>
              Target:{" "}
              <span className="font-data text-ink">
                {preflight?.render_database?.postgres_name ||
                  preflight?.render_database?.display_url ||
                  "unknown"}
              </span>
            </p>
            <p>
              Location:{" "}
              <span className="font-data text-ink">
                {preflight?.render_database?.display_url || "unknown"}
              </span>
            </p>
            <p>
              Resolution:{" "}
              <span className="font-data text-ink">
                {preflight?.render_database_source === "render_api"
                  ? "Render API"
                  : "Direct env var"}
              </span>
            </p>
            <p>
              Local items / hosted items:{" "}
              <span className="font-data text-ink">
                {preflight?.source_summary?.toolkit_item_count ?? "?"} /{" "}
                {preflight?.target_summary?.toolkit_item_count ?? "?"}
              </span>
            </p>
          </>
        )}
      </div>
      {result && (
        <p
          className={`mt-3 font-ui text-sm ${isError ? "text-danger" : "text-valid"}`}
        >
          {isError
            ? result.error
            : `${result.message} Local items: ${result.source_summary?.toolkit_item_count ?? "?"}. Hosted items: ${result.target_after_summary?.toolkit_item_count ?? "?"}. Duration: ${result.duration_seconds ?? "?"}s.`}
        </p>
      )}
    </div>
  );
}
