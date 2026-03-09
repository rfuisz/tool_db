import type { WorkflowStep, WorkflowStepType } from "./types";

export type WorkflowPhaseKey = "design" | "build" | "test" | "learn";

type WorkflowPhaseDefinition = {
  key: WorkflowPhaseKey;
  label: string;
  description: string;
  stepTypes: WorkflowStepType[];
};

export type WorkflowPhaseSummary = WorkflowPhaseDefinition & {
  steps: WorkflowStep[];
  stageNames: string[];
  totalHours: number;
  totalCost: number;
  parallelizableCount: number;
  retryRiskCount: number;
};

export const WORKFLOW_PHASES: WorkflowPhaseDefinition[] = [
  {
    key: "design",
    label: "Design",
    description: "Define the construct, library, or study plan.",
    stepTypes: ["design"],
  },
  {
    key: "build",
    label: "Build",
    description: "Make or prepare the material you will evaluate.",
    stepTypes: [
      "dna_acquisition",
      "assembly",
      "transformation",
      "colony_screen",
      "sequence_verification",
      "transfection",
      "expression",
      "packaging",
      "delivery",
    ],
  },
  {
    key: "test",
    label: "Test",
    description: "Run the assay or selection that produces signal.",
    stepTypes: ["selection_round", "assay"],
  },
  {
    key: "learn",
    label: "Learn",
    description: "Interpret the result and decide what to do next.",
    stepTypes: ["analysis", "decision"],
  },
];

export function getWorkflowPhases(
  steps: WorkflowStep[],
  options: { includeEmpty?: boolean } = {},
): WorkflowPhaseSummary[] {
  return WORKFLOW_PHASES.map((phase) => {
    const phaseSteps = steps.filter((step) => phase.stepTypes.includes(step.step_type));
    const stageNames = Array.from(
      new Set(
        phaseSteps
          .map((step) => step.stage_name)
          .filter((value): value is string => Boolean(value)),
      ),
    );

    return {
      ...phase,
      steps: phaseSteps,
      stageNames,
      totalHours: phaseSteps.reduce(
        (sum, step) => sum + (step.duration_typical_hours ?? 0),
        0,
      ),
      totalCost: phaseSteps.reduce(
        (sum, step) => sum + (step.direct_cost_usd_typical ?? 0),
        0,
      ),
      parallelizableCount: phaseSteps.filter((step) => step.parallelizable).length,
      retryRiskCount: phaseSteps.filter(
        (step) => (step.failure_probability ?? 0) > 0.05,
      ).length,
    };
  }).filter((phase) => options.includeEmpty || phase.steps.length > 0);
}
