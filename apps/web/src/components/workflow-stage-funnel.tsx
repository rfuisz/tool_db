"use client";

import type { WorkflowStage, WorkflowStep } from "@/lib/types";
import {
  WORKFLOW_SEARCH_MODALITY_LABELS,
  WORKFLOW_STAGE_KIND_LABELS,
} from "@/lib/vocabularies";

function formatCandidateCount(
  count: number | null,
  unit: string | null,
): string | null {
  if (count === null) {
    return null;
  }
  if (!unit) {
    return count.toLocaleString();
  }
  return `${count.toLocaleString()} ${unit}`;
}

function stageSteps(
  stage: WorkflowStage,
  steps: WorkflowStep[],
): WorkflowStep[] {
  return steps.filter((step) => step.stage_name === stage.stage_name);
}

export function WorkflowStageFunnel({
  stages,
  steps,
}: {
  stages: WorkflowStage[];
  steps: WorkflowStep[];
}) {
  if (stages.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border border-edge bg-surface-alt p-5">
      <div className="mb-4">
        <p className="small-caps mb-2">Screening Funnel</p>
        <p className="max-w-3xl text-sm leading-6 text-ink-secondary">
          Higher-level screening gates show how the workflow narrows candidate
          space before the detailed step-by-step timeline.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {stages.map((stage, index) => {
          const mappedSteps = stageSteps(stage, steps);
          const counts = [
            formatCandidateCount(
              stage.input_candidate_count_typical,
              stage.candidate_unit,
            ),
            formatCandidateCount(
              stage.output_candidate_count_typical,
              stage.candidate_unit,
            ),
          ];

          return (
            <div
              key={stage.id}
              className="rounded-lg border border-edge bg-surface p-4"
            >
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span className="font-data text-xs text-ink-muted">
                  {index + 1}
                </span>
                <h3 className="font-display text-lg text-ink">
                  {stage.stage_name}
                </h3>
                <span className="rounded-full bg-surface-alt px-2 py-1 font-ui text-[11px] text-ink-muted">
                  {WORKFLOW_STAGE_KIND_LABELS[stage.stage_kind]}
                </span>
                {stage.search_modality && (
                  <span className="rounded-full bg-brand-light px-2 py-1 font-ui text-[11px] text-brand">
                    {WORKFLOW_SEARCH_MODALITY_LABELS[stage.search_modality]}
                  </span>
                )}
                {stage.higher_fidelity_than_previous && (
                  <span className="rounded-full bg-valid-light px-2 py-1 font-ui text-[11px] text-valid">
                    higher fidelity
                  </span>
                )}
              </div>

              {(counts[0] || counts[1]) && (
                <p className="mb-3 font-data text-xs text-ink-muted">
                  {counts[0] ?? "unknown"}
                  {" -> "}
                  {counts[1] ?? "unknown"}
                </p>
              )}

              {stage.selection_basis && (
                <p className="mb-3 text-sm leading-6 text-ink-secondary">
                  {stage.selection_basis}
                </p>
              )}

              {mappedSteps.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {mappedSteps.map((step) => (
                    <span
                      key={step.id}
                      className="rounded-md border border-edge bg-surface-alt px-2.5 py-1.5 font-ui text-xs text-ink-secondary"
                    >
                      {step.step_name}
                    </span>
                  ))}
                </div>
              )}

              {stage.advance_criteria && (
                <p className="text-sm leading-6 text-ink-secondary">
                  Advance when: {stage.advance_criteria}
                </p>
              )}

              {stage.bottleneck_risk && (
                <p className="mt-2 text-sm leading-6 text-caution">
                  Bottleneck risk: {stage.bottleneck_risk}
                </p>
              )}

              {stage.enriches_for_axes.length > 0 && (
                <p className="mt-2 text-sm leading-6 text-ink-secondary">
                  Enriches for: {stage.enriches_for_axes.join(", ")}
                </p>
              )}

              {stage.guards_against_axes.length > 0 && (
                <p className="mt-2 text-sm leading-6 text-ink-secondary">
                  Guards against: {stage.guards_against_axes.join(", ")}
                </p>
              )}

              {stage.preserves_downstream_property_axes.length > 0 && (
                <p className="mt-2 text-sm leading-6 text-ink-secondary">
                  Preserves downstream:{" "}
                  {stage.preserves_downstream_property_axes.join(", ")}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
