import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/backend-data";
import { isLocalAdminEnabled } from "@/lib/first-pass-access";

export const runtime = "nodejs";

export async function GET() {
  if (!(await isLocalAdminEnabled())) {
    return NextResponse.json(
      { error: "Render DB sync is only available from localhost." },
      { status: 403 },
    );
  }

  const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/sync-render-db`, {
    method: "GET",
    cache: "no-store",
  });
  const payload = await response.json().catch(() => ({
    error: "Render DB sync preflight failed with a non-JSON response.",
  }));

  return NextResponse.json(payload, { status: response.status });
}

export async function POST() {
  if (!(await isLocalAdminEnabled())) {
    return NextResponse.json(
      { error: "Render DB sync is only available from localhost." },
      { status: 403 },
    );
  }

  const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/sync-render-db`, {
    method: "POST",
    cache: "no-store",
  });
  const payload = await response.json().catch(() => ({
    error: "Render DB sync failed with a non-JSON response.",
  }));

  return NextResponse.json(payload, { status: response.status });
}
