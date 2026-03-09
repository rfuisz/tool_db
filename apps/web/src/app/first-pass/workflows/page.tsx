import { notFound } from "next/navigation";

import { FirstPassBrowseClient } from "@/components/first-pass-browse-client";
import { getFirstPassEntities } from "@/lib/backend-data";
import { isFirstPassEnabled } from "@/lib/first-pass-access";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function FirstPassWorkflowsPage() {
  if (!(await isFirstPassEnabled())) {
    notFound();
  }

  const entities = await getFirstPassEntities();

  return (
    <FirstPassBrowseClient
      entities={entities}
      defaultScope="workflows"
      title="First-pass extracted workflows"
      description="Workflow-template candidates and their linked provenance are surfaced here so stage structure can be inspected before workflow canonicalization."
    />
  );
}
