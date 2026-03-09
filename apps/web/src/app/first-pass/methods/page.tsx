import { notFound } from "next/navigation";

import { FirstPassBrowseClient } from "@/components/first-pass-browse-client";
import { getFirstPassEntities } from "@/lib/backend-data";
import { isFirstPassEnabled } from "@/lib/first-pass-access";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function FirstPassMethodsPage() {
  if (!(await isFirstPassEnabled())) {
    notFound();
  }

  const entities = await getFirstPassEntities();

  return (
    <FirstPassBrowseClient
      entities={entities}
      defaultScope="methods"
      title="First-pass extracted methods"
      description="Method-like toolkit candidates such as engineering methods, assay methods, and computational methods are separated here so they can be reviewed and canonicalized without getting buried in the broader item list."
    />
  );
}
