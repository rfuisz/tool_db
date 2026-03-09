import { getExtractedWorkflows } from "@/lib/backend-data";
import { searchExtractedWorkflows } from "@/lib/api-search";
import { WorkflowsBrowseClient } from "@/components/workflows-browse-client";

function collectUnique(
  workflows: { target_mechanisms: string[]; target_techniques: string[] }[],
  key: "target_mechanisms" | "target_techniques",
): string[] {
  const set = new Set<string>();
  for (const wf of workflows) {
    for (const v of wf[key]) set.add(v);
  }
  return Array.from(set).sort();
}

export default async function WorkflowsPage() {
  const allWorkflows = await getExtractedWorkflows();
  const initial = searchExtractedWorkflows(allWorkflows, {
    sort: "richness",
    limit: 50,
    offset: 0,
  });

  return (
    <WorkflowsBrowseClient
      initialWorkflows={initial.results}
      initialTotal={initial.total}
      filterOptions={{
        mechanisms: collectUnique(allWorkflows, "target_mechanisms"),
        techniques: collectUnique(allWorkflows, "target_techniques"),
      }}
    />
  );
}
