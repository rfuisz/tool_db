import { NextResponse } from "next/server";

import { getItemBySlug } from "@/lib/data";

interface RouteContext {
  params: Promise<{ slug: string }>;
}

export async function GET(_request: Request, context: RouteContext) {
  const { slug } = await context.params;
  const item = getItemBySlug(slug);

  if (!item) {
    return NextResponse.json({ error: `Item not found for slug "${slug}".` }, { status: 404 });
  }

  return NextResponse.json(item);
}
