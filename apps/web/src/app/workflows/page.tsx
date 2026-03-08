import { WorkflowAccordion } from "@/components/workflow-accordion";
import { getWorkflows } from "@/lib/backend-data";

export default async function WorkflowsPage() {
  const workflows = await getWorkflows();

  return (
    <div>
      <header className="mb-16">
        <h1 className="mb-3">Workflows</h1>
        <p className="max-w-xl text-lg text-ink-secondary">
          Design&#x2013;Build&#x2013;Test&#x2013;Learn loop archetypes with
          step-level timing and cost estimates.
        </p>
      </header>

      <WorkflowAccordion workflows={workflows} />
    </div>
  );
}
