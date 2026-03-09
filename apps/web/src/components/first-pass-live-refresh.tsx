"use client";

import { useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

const REFRESH_INTERVAL_MS = 5000;

function formatSecondsRemaining(msRemaining: number): number {
  return Math.max(1, Math.ceil(msRemaining / 1000));
}

export function FirstPassLiveRefresh() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [lastRefreshedAt, setLastRefreshedAt] = useState(() => Date.now());
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const tickTimer = window.setInterval(() => {
      setNow(Date.now());
    }, 1000);

    const refreshTimer = window.setInterval(() => {
      if (document.visibilityState !== "visible") {
        return;
      }
      startTransition(() => {
        router.refresh();
        setLastRefreshedAt(Date.now());
      });
    }, REFRESH_INTERVAL_MS);

    return () => {
      window.clearInterval(tickTimer);
      window.clearInterval(refreshTimer);
    };
  }, [router]);

  const msUntilRefresh = REFRESH_INTERVAL_MS - ((now - lastRefreshedAt) % REFRESH_INTERVAL_MS);

  return (
    <div className="flex flex-wrap items-center gap-3 font-ui text-xs text-ink-muted">
      <span>
        Live refresh {isPending ? "running" : `every ${REFRESH_INTERVAL_MS / 1000}s`}
      </span>
      <span>Next refresh in {formatSecondsRemaining(msUntilRefresh)}s</span>
      <button
        type="button"
        onClick={() => {
          startTransition(() => {
            router.refresh();
            setLastRefreshedAt(Date.now());
          });
        }}
        className="text-brand hover:text-accent"
      >
        Refresh now
      </button>
    </div>
  );
}
