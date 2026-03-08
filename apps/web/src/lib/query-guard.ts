import "server-only";

type RateLimitRecord = {
  count: number;
  resetAt: number;
};

export interface QueryRequestGuardResult {
  ok: boolean;
  status?: number;
  error?: string;
  headers?: Record<string, string>;
}

const rateLimitStore = new Map<string, RateLimitRecord>();

function getRequiredApiKey(): string {
  return (
    process.env.TOOL_DB_QUERY_CLIENT_API_KEY ??
    process.env.TOOL_DB_QUERY_API_KEY ??
    ""
  ).trim();
}

function getRateLimitWindowMs(): number {
  const rawValue = Number(
    process.env.TOOL_DB_QUERY_RATE_LIMIT_WINDOW_MS ?? 60_000,
  );
  return Number.isFinite(rawValue) && rawValue > 0
    ? Math.trunc(rawValue)
    : 60_000;
}

function getRateLimitMaxRequests(): number {
  const rawValue = Number(
    process.env.TOOL_DB_QUERY_RATE_LIMIT_MAX_REQUESTS ?? 0,
  );
  return Number.isFinite(rawValue) && rawValue > 0 ? Math.trunc(rawValue) : 0;
}

function getClientIp(request: Request): string {
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) {
    return forwardedFor.split(",")[0]?.trim() || "unknown";
  }

  return request.headers.get("x-real-ip")?.trim() || "unknown";
}

function cleanupExpiredEntries(now: number) {
  for (const [key, record] of rateLimitStore.entries()) {
    if (record.resetAt <= now) {
      rateLimitStore.delete(key);
    }
  }
}

function validateSharedApiKey(
  request: Request,
): QueryRequestGuardResult | null {
  const requiredApiKey = getRequiredApiKey();
  if (!requiredApiKey) {
    return null;
  }

  const providedApiKey =
    request.headers.get("x-api-key")?.trim() ||
    request.headers
      .get("authorization")
      ?.replace(/^Bearer\s+/i, "")
      .trim() ||
    "";

  if (providedApiKey !== requiredApiKey) {
    return {
      ok: false,
      status: 401,
      error:
        "Unauthorized. Provide a valid API key via x-api-key or Authorization: Bearer.",
    };
  }

  return null;
}

function enforceRateLimit(request: Request): QueryRequestGuardResult | null {
  const maxRequests = getRateLimitMaxRequests();
  if (maxRequests < 1) {
    return null;
  }

  const now = Date.now();
  cleanupExpiredEntries(now);

  const windowMs = getRateLimitWindowMs();
  const clientIp = getClientIp(request);
  const record = rateLimitStore.get(clientIp);

  if (!record || record.resetAt <= now) {
    rateLimitStore.set(clientIp, { count: 1, resetAt: now + windowMs });
    return {
      ok: true,
      headers: {
        "X-RateLimit-Limit": String(maxRequests),
        "X-RateLimit-Remaining": String(maxRequests - 1),
        "X-RateLimit-Reset": String(now + windowMs),
      },
    };
  }

  if (record.count >= maxRequests) {
    const retryAfterSeconds = Math.max(
      1,
      Math.ceil((record.resetAt - now) / 1000),
    );
    return {
      ok: false,
      status: 429,
      error: "Rate limit exceeded for /api/query.",
      headers: {
        "Retry-After": String(retryAfterSeconds),
        "X-RateLimit-Limit": String(maxRequests),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": String(record.resetAt),
      },
    };
  }

  record.count += 1;
  rateLimitStore.set(clientIp, record);

  return {
    ok: true,
    headers: {
      "X-RateLimit-Limit": String(maxRequests),
      "X-RateLimit-Remaining": String(Math.max(0, maxRequests - record.count)),
      "X-RateLimit-Reset": String(record.resetAt),
    },
  };
}

export function guardQueryRequest(request: Request): QueryRequestGuardResult {
  const authFailure = validateSharedApiKey(request);
  if (authFailure) {
    return authFailure;
  }

  return enforceRateLimit(request) ?? { ok: true };
}
