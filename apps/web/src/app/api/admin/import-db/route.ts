import { NextResponse } from "next/server";

import { getApiBaseUrl } from "@/lib/backend-data";

export const runtime = "nodejs";

function forwardHeaders(request: Request): Headers {
  const headers = new Headers();
  const xApiKey = request.headers.get("x-api-key");
  const authorization = request.headers.get("authorization");
  const contentEncoding = request.headers.get("content-encoding");
  const contentType = request.headers.get("content-type");

  if (xApiKey) {
    headers.set("x-api-key", xApiKey);
  }
  if (authorization) {
    headers.set("authorization", authorization);
  }
  if (contentEncoding) {
    headers.set("content-encoding", contentEncoding);
  }
  if (contentType) {
    headers.set("content-type", contentType);
  }

  return headers;
}

async function readPayload(response: Response, fallbackError: string): Promise<Record<string, unknown>> {
  const payload = await response.json().catch(() => ({ error: fallbackError }));
  return (payload ?? { error: fallbackError }) as Record<string, unknown>;
}

export async function GET(request: Request) {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/import-db`, {
    method: "GET",
    cache: "no-store",
    headers: forwardHeaders(request),
  });
  const payload = await readPayload(
    response,
    "Hosted database import preflight failed with a non-JSON response.",
  );
  return NextResponse.json(payload, { status: response.status });
}

export async function POST(request: Request) {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/admin/import-db`, {
    method: "POST",
    cache: "no-store",
    headers: forwardHeaders(request),
    body: Buffer.from(await request.arrayBuffer()),
  });
  const payload = await readPayload(
    response,
    "Hosted database import failed with a non-JSON response.",
  );
  return NextResponse.json(payload, { status: response.status });
}
