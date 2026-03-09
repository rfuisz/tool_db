import { notFound, redirect } from "next/navigation";

import { isFirstPassEnabled } from "@/lib/first-pass-access";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function FirstPassItemPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  if (!(await isFirstPassEnabled())) {
    notFound();
  }

  const { slug } = await params;
  redirect(`/first-pass/entities/toolkit_item/${slug}`);
}
