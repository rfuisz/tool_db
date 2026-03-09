import { execSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { NextResponse } from "next/server";

import { isLocalAdminEnabled } from "@/lib/first-pass-access";

export const runtime = "nodejs";

const MAX_BUFFER_BYTES = 256 * 1024 * 1024;

function loadRepoEnv(): Record<string, string> {
  const candidates = [
    path.resolve(process.cwd(), ".env"),
    path.resolve(process.cwd(), "..", "..", ".env"),
  ];
  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      const vars: Record<string, string> = {};
      for (const line of readFileSync(candidate, "utf8").split("\n")) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("#")) continue;
        const eqIdx = trimmed.indexOf("=");
        if (eqIdx < 1) continue;
        vars[trimmed.slice(0, eqIdx).trim()] = trimmed.slice(eqIdx + 1).trim();
      }
      return vars;
    }
  }
  return {};
}

function envVar(key: string): string {
  const value = (process.env[key] ?? "").trim();
  if (value) return value;
  const repoEnv = loadRepoEnv();
  return (repoEnv[key] ?? "").trim();
}

function getRepoRoot(): string {
  const cwd = process.cwd();
  if (existsSync(path.join(cwd, "apps", "web"))) return cwd;
  return path.resolve(cwd, "..", "..");
}

function getPythonPath(): string {
  const venv = path.join(getRepoRoot(), ".venv", "bin", "python");
  return existsSync(venv) ? venv : "python3";
}

function getPgBinDir(): string {
  if (existsSync("/opt/homebrew/opt/libpq/bin")) return "/opt/homebrew/opt/libpq/bin";
  if (existsSync("/usr/local/opt/libpq/bin")) return "/usr/local/opt/libpq/bin";
  return "";
}

function getLocalDatabaseUrl(): string {
  const url = envVar("DATABASE_URL");
  if (!url) throw new Error("DATABASE_URL is not set.");
  return url;
}

function getRenderExternalUrl(): string {
  const url = envVar("RENDER_POSTGRES_EXTERNAL_URL");
  if (!url) throw new Error("RENDER_POSTGRES_EXTERNAL_URL is not set.");
  return url;
}

function shellEnv(): NodeJS.ProcessEnv {
  const pgBin = getPgBinDir();
  const repoRoot = getRepoRoot();
  return {
    ...process.env,
    ...(pgBin ? { PATH: `${pgBin}:${process.env.PATH ?? ""}` } : {}),
    PYTHONPATH: [process.env.PYTHONPATH, path.join(repoRoot, "src")]
      .filter(Boolean)
      .join(":"),
  };
}

function queryCount(databaseUrl: string, table: string): number {
  const out = execSync(
    `psql "${databaseUrl}" -t -A -c "SELECT count(*) FROM ${table};"`,
    { env: shellEnv(), encoding: "utf8", maxBuffer: MAX_BUFFER_BYTES },
  );
  return parseInt(out.trim(), 10);
}

function respond(body: Record<string, unknown>, status = 200) {
  return NextResponse.json(body, { status });
}

export async function GET() {
  if (!(await isLocalAdminEnabled())) {
    return respond({ error: "Only available from localhost." }, 403);
  }

  try {
    const localUrl = getLocalDatabaseUrl();
    const renderUrl = getRenderExternalUrl();
    const localItems = queryCount(localUrl, "toolkit_item");
    const renderItems = queryCount(renderUrl, "toolkit_item");
    return respond({
      status: "ready",
      local_items: localItems,
      render_items: renderItems,
    });
  } catch (error) {
    return respond(
      { error: error instanceof Error ? error.message : "Preflight failed." },
      500,
    );
  }
}

export async function POST(request: Request) {
  if (!(await isLocalAdminEnabled())) {
    return respond({ error: "Only available from localhost." }, 403);
  }

  try {
    const localUrl = getLocalDatabaseUrl();
    const renderUrl = getRenderExternalUrl();
    const url = new URL(request.url);
    const mode = url.searchParams.get("mode") ?? "incremental";
    const fullFlag = mode === "full" ? " --full" : "";

    const pythonPath = getPythonPath();
    const stdout = execSync(
      `${pythonPath} -m tool_db_backend.incremental_sync "${localUrl}" "${renderUrl}"${fullFlag}`,
      {
        cwd: getRepoRoot(),
        env: shellEnv(),
        encoding: "utf8",
        maxBuffer: MAX_BUFFER_BYTES,
        timeout: 300_000,
      },
    );

    const report = JSON.parse(stdout) as Record<string, unknown>;
    return respond(report);
  } catch (error) {
    return respond(
      { error: error instanceof Error ? error.message : "Sync failed." },
      500,
    );
  }
}
