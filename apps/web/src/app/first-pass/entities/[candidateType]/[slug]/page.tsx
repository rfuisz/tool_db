import { notFound } from "next/navigation";

import { FirstPassEntityDetailView } from "@/components/first-pass-entity-detail";
import { getFirstPassEntityByKey } from "@/lib/backend-data";
import { isFirstPassEnabled } from "@/lib/first-pass-access";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function FirstPassEntityPage({
  params,
}: {
  params: Promise<{ candidateType: string; slug: string }>;
}) {
  if (!(await isFirstPassEnabled())) {
    notFound();
  }

  const { candidateType, slug } = await params;
  const entity = await getFirstPassEntityByKey(candidateType, slug);

  if (!entity) {
    notFound();
  }

  return <FirstPassEntityDetailView entity={entity} />;
}
