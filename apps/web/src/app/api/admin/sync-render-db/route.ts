import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { gzipSync } from "node:zlib";

import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/backend-data";
import { isLocalAdminEnabled } from "@/lib/first-pass-access";

export const runtime = "nodejs";

const MAX_BUFFER_BYTES = 256 * 1024 * 1024;

type SyncPayload = Record<string, unknown> & {
  source_summary?: {
    toolkit_item_count?: number;
    first_pass_distinct_slug_count?: number;
  };
};

function getHostedSyncConfig():
  | { targetUrl: string; adminSyncKey: string }
  | null {
  const targetUrl = (process.env.TOOL_DB_SYNC_TARGET_URL ?? "")
    .trim()
    .replace(/\/$/, "");
  const adminSyncKey = (process.env.TOOL_DB_ADMIN_SYNC_KEY ?? "").trim();
  if (targetUrl && adminSyncKey) {
    return { targetUrl, adminSyncKey };
  }

  if (targetUrl || adminSyncKey) {
    throw new Error(
      "Set both TOOL_DB_SYNC_TARGET_URL and TOOL_DB_ADMIN_SYNC_KEY to enable hosted import sync.",
    );
  }

  return null;
}

function getRepoRoot(): string {
  const cwd = process.cwd();
  if (existsSync(path.join(cwd, "apps", "web"))) {
    return cwd;
  }
  return path.resolve(cwd, "..", "..");
}

function getPythonPath(repoRoot: string): string {
  const venvPython = path.join(repoRoot, ".venv", "bin", "python");
  return existsSync(venvPython) ? venvPython : "python3";
}

function getPgDumpPath(): string {
  const configuredPath = (process.env.PG_DUMP_PATH ?? "").trim();
  if (configuredPath) {
    return configuredPath;
  }

  const homebrewPath = "/opt/homebrew/opt/libpq/bin/pg_dump";
  return existsSync(homebrewPath) ? homebrewPath : "pg_dump";
}

function getLocalDatabaseUrl(): string {
  const databaseUrl = (process.env.DATABASE_URL ?? "").trim();
  if (!databaseUrl) {
    throw new Error("DATABASE_URL must be set before syncing.");
  }

  return databaseUrl;
}

function readLocalDatabaseSummary(): SyncPayload["source_summary"] {
  const repoRoot = getRepoRoot();
  const pythonPath = getPythonPath(repoRoot);
  const stdout = execFileSync(
    pythonPath,
    [
      "-c",
      [
        "import json",
        "from tool_db_backend.config import get_settings",
        "from tool_db_backend.render_db_sync import _read_database_summary",
        "settings = get_settings()",
        "print(json.dumps(_read_database_summary(settings.database_url)))",
      ].join("; "),
    ],
    {
      cwd: repoRoot,
      env: {
        ...process.env,
        PYTHONPATH: [process.env.PYTHONPATH, "src"].filter(Boolean).join(":"),
      },
      encoding: "utf8",
      maxBuffer: MAX_BUFFER_BYTES,
    },
  );
  return JSON.parse(stdout) as SyncPayload["source_summary"];
}

function dumpLocalDatabaseSql(): Buffer {
  const dumpOutput = execFileSync(
    getPgDumpPath(),
    [
      "--data-only",
      "--inserts",
      "--no-owner",
      "--no-privileges",
      "--dbname",
      getLocalDatabaseUrl(),
    ],
    {
      cwd: getRepoRoot(),
      env: process.env,
      maxBuffer: MAX_BUFFER_BYTES,
    },
  );
  return Buffer.isBuffer(dumpOutput)
    ? dumpOutput
    : Buffer.from(dumpOutput, "utf8");
}

async function readJsonPayload(
  response: Response,
  fallbackError: string,
): Promise<SyncPayload> {
  const payload = await response.json().catch(() => ({ error: fallbackError }));
  return (payload ?? { error: fallbackError }) as SyncPayload;
}

function respond(payload: SyncPayload, status: number): NextResponse {
  return NextResponse.json(payload, { status });
}

export async function GET() {
  if (!(await isLocalAdminEnabled())) {
    return respond(
      { error: "Render DB sync is only available from localhost." },
      403,
    );
  }

  try {
    const hostedSyncConfig = getHostedSyncConfig();
    if (hostedSyncConfig) {
      const [sourceSummary, response] = await Promise.all([
        Promise.resolve().then(readLocalDatabaseSummary),
        fetch(`${hostedSyncConfig.targetUrl}/api/admin/import-db`, {
          method: "GET",
          cache: "no-store",
          headers: { "x-api-key": hostedSyncConfig.adminSyncKey },
        }),
      ]);
      const payload = await readJsonPayload(
        response,
        "Hosted database import preflight failed with a non-JSON response.",
      );
      return respond({ ...payload, source_summary: sourceSummary }, response.status);
    }

    const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/sync-render-db`, {
      method: "GET",
      cache: "no-store",
    });
    const payload = await readJsonPayload(
      response,
      "Render DB sync preflight failed with a non-JSON response.",
    );
    return respond(payload, response.status);
  } catch (error) {
    return respond(
      {
        error:
          error instanceof Error
            ? error.message
            : "Render DB sync preflight failed.",
      },
      500,
    );
  }
}

export async function POST() {
  if (!(await isLocalAdminEnabled())) {
    return respond(
      { error: "Render DB sync is only available from localhost." },
      403,
    );
  }

  try {
    const hostedSyncConfig = getHostedSyncConfig();
    if (hostedSyncConfig) {
      const sourceSummary = readLocalDatabaseSummary();
      const compressedDump = gzipSync(dumpLocalDatabaseSql());
      const response = await fetch(`${hostedSyncConfig.targetUrl}/api/admin/import-db`, {
        method: "POST",
        cache: "no-store",
        headers: {
          "content-encoding": "gzip",
          "content-type": "application/sql; charset=utf-8",
          "x-api-key": hostedSyncConfig.adminSyncKey,
        },
        body: compressedDump,
      });
      const payload = await readJsonPayload(
        response,
        "Hosted database import failed with a non-JSON response.",
      );
      return respond({ ...payload, source_summary: sourceSummary }, response.status);
    }

    const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/sync-render-db`, {
      method: "POST",
      cache: "no-store",
    });
    const payload = await readJsonPayload(
      response,
      "Render DB sync failed with a non-JSON response.",
    );
    return respond(payload, response.status);
  } catch (error) {
    return respond(
      {
        error:
          error instanceof Error ? error.message : "Render DB sync failed.",
      },
      500,
    );
  }
}
