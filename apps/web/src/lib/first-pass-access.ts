import "server-only";

import { headers } from "next/headers";

function isLocalHost(hostname: string): boolean {
  const normalized = hostname.trim().toLowerCase();
  return normalized === "localhost" || normalized === "127.0.0.1";
}

export async function isFirstPassEnabled(): Promise<boolean> {
  if (process.env.RENDER || process.env.RENDER_EXTERNAL_URL) {
    return false;
  }

  const requestHeaders = await headers();
  const hostHeader = requestHeaders.get("x-forwarded-host") ?? requestHeaders.get("host") ?? "";
  const hostname = hostHeader.split(":")[0];
  return isLocalHost(hostname);
}
