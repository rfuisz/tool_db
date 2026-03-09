import { headers } from "next/headers";

function getApiTarget(): string | null {
  const internalHost = process.env.TOOL_DB_API_HOST?.trim();
  if (internalHost) {
    const internalPort = process.env.TOOL_DB_API_PORT?.trim() || "8000";
    return `${internalHost}:${internalPort}`;
  }

  const directBaseUrl =
    process.env.TOOL_DB_API_BASE_URL?.trim() ||
    process.env.NEXT_PUBLIC_TOOL_DB_API_BASE_URL?.trim();
  if (!directBaseUrl) {
    return null;
  }

  return directBaseUrl.replace(/^https?:\/\//, "").replace(/\/$/, "");
}

function isLocalHost(host: string | null): boolean {
  if (!host) {
    return false;
  }
  return host.startsWith("localhost") || host.startsWith("127.0.0.1");
}

function getDeploymentParts(requestHost: string | null): string[] {
  const service =
    process.env.RENDER_SERVICE_NAME?.trim() ||
    process.env.VERCEL_PROJECT_PRODUCTION_URL?.trim() ||
    requestHost;
  const branch =
    process.env.RENDER_GIT_BRANCH?.trim() ||
    process.env.VERCEL_GIT_COMMIT_REF?.trim();
  const commit =
    process.env.RENDER_GIT_COMMIT?.trim() ||
    process.env.VERCEL_GIT_COMMIT_SHA?.trim();

  return [
    service,
    branch,
    commit ? commit.slice(0, 7) : null,
  ].filter((part): part is string => Boolean(part));
}

export async function DeploymentBadge() {
  const headerStore = await headers();
  const requestHost =
    headerStore.get("x-forwarded-host")?.trim() ||
    headerStore.get("host")?.trim() ||
    null;
  const deploymentParts = getDeploymentParts(requestHost);
  const apiTarget = getApiTarget();

  if (isLocalHost(requestHost) && !apiTarget) {
    return null;
  }

  if (deploymentParts.length === 0 && !apiTarget) {
    return null;
  }

  return (
    <div className="border border-edge bg-surface-alt px-3 py-2 font-data text-[11px] leading-relaxed text-ink-muted">
      {deploymentParts.length > 0 ? (
        <p>Serving: {deploymentParts.join(" · ")}</p>
      ) : null}
      {apiTarget ? <p>API: {apiTarget}</p> : null}
    </div>
  );
}
