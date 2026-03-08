"use client";

import { useEffect, useState } from "react";
import { WorkflowPhaseBreakdown } from "@/components/workflow-phase-breakdown";
import { WorkflowStageFunnel } from "@/components/workflow-stage-funnel";
import { WorkflowTimeline } from "@/components/workflow-timeline";
import type { WorkflowTemplate } from "@/lib/types";
import { WORKFLOW_FAMILY_LABELS } from "@/lib/vocabularies";

function formatDurationDays(hours: number): string {
  return `~${Math.max(1, Math.round(hours / 24))}d`;
}

function formatCost(usd: number): string {
  return `$${usd.toLocaleString()}`;
}

export function WorkflowAccordion({
  workflows,
}: {
  workflows: WorkflowTemplate[];
}) {
  const [openSlug, setOpenSlug] = useState<string | null>(
    workflows[0]?.slug ?? null,
  );

  useEffect(() => {
    const syncHash = () => {
      const slug = window.location.hash.replace(/^#/, "");
      if (!slug) {
        return;
      }
      if (workflows.some((workflow) => workflow.slug === slug)) {
        setOpenSlug(slug);
        requestAnimationFrame(() => {
          document
            .getElementById(slug)
            ?.scrollIntoView({ block: "start", behavior: "smooth" });
        });
      }
    };

    syncHash();
    window.addEventListener("hashchange", syncHash);
    return () => window.removeEventListener("hashchange", syncHash);
  }, [workflows]);

  const toggleWorkflow = (slug: string) => {
    const next = openSlug === slug ? null : slug;
    const url = new URL(window.location.href);

    if (next) {
      url.hash = next;
    } else {
      url.hash = "";
    }

    window.history.replaceState(null, "", url);
    setOpenSlug(next);
  };

  return (
    <div className="space-y-4">
      {workflows.map((workflow) => {
        const isOpen = openSlug === workflow.slug;
        const totalHours = workflow.steps.reduce(
          (sum, step) => sum + (step.duration_typical_hours ?? 0),
          0,
        );
        const totalCost = workflow.steps.reduce(
          (sum, step) => sum + (step.direct_cost_usd_typical ?? 0),
          0,
        );

        return (
          <section
            key={workflow.id}
            id={workflow.slug}
            className="rounded-lg border border-edge bg-surface"
          >
            <button
              type="button"
              aria-expanded={isOpen}
              aria-controls={`${workflow.slug}-details`}
              onClick={() => toggleWorkflow(workflow.slug)}
              className="w-full p-6 text-left transition-colors hover:bg-surface-alt"
            >
              <div className="flex items-start justify-between gap-6">
                <div className="min-w-0">
                  <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1">
                    <h2 className="text-ink">{workflow.name}</h2>
                    <span className="font-ui text-sm text-ink-muted">
                      {WORKFLOW_FAMILY_LABELS[workflow.workflow_family]}
                      {workflow.throughput_class && (
                        <>
                          {" "}
                          &middot;{" "}
                          {workflow.throughput_class.replace(/_/g, " ")}
                        </>
                      )}
                    </span>
                  </div>
                  <p className="max-w-3xl text-[15px] text-ink-secondary">
                    {workflow.objective}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 font-data text-xs text-ink-muted">
                    {workflow.stages && workflow.stages.length > 0 && (
                      <span>{workflow.stages.length} stages</span>
                    )}
                    <span>{workflow.steps.length} steps</span>
                    <span>{formatDurationDays(totalHours)}</span>
                    <span>{formatCost(totalCost)}</span>
                    {workflow.recommended_for && (
                      <span className="font-ui">
                        Recommended for: {workflow.recommended_for}
                      </span>
                    )}
                  </div>
                </div>
                <span className="shrink-0 font-data text-sm text-ink-muted">
                  {isOpen ? "Close" : "Open"}
                </span>
              </div>
            </button>

            {isOpen && (
              <div
                id={`${workflow.slug}-details`}
                className="border-t border-edge px-6 pt-6 pb-6"
              >
                {workflow.stages && workflow.stages.length > 0 && (
                  <div className="mb-6">
                    <WorkflowStageFunnel
                      stages={workflow.stages}
                      steps={workflow.steps}
                    />
                  </div>
                )}

                <div className="mb-6">
                  <WorkflowPhaseBreakdown steps={workflow.steps} />
                </div>

                <div className="rounded-lg bg-surface-alt p-6">
                  <WorkflowTimeline steps={workflow.steps} />
                </div>

                {(workflow.simple_summary ||
                  (workflow.how_to_implement &&
                    workflow.how_to_implement.length > 0) ||
                  (workflow.used_when && workflow.used_when.length > 0) ||
                  (workflow.tradeoffs && workflow.tradeoffs.length > 0) ||
                  (workflow.citations && workflow.citations.length > 0)) && (
                  <div className="mt-6 grid gap-4 lg:grid-cols-2">
                    {workflow.simple_summary && (
                      <div className="rounded-lg border border-edge bg-surface-alt p-5">
                        <p className="small-caps mb-3">Simple Summary</p>
                        <p className="text-sm leading-6 text-ink-secondary">
                          {workflow.simple_summary}
                        </p>
                      </div>
                    )}

                    {workflow.used_when && workflow.used_when.length > 0 && (
                      <div className="rounded-lg border border-edge bg-surface-alt p-5">
                        <p className="small-caps mb-3">Used When</p>
                        <ul className="space-y-2 text-sm leading-6 text-ink-secondary">
                          {workflow.used_when.map((note) => (
                            <li key={note}>{note}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {workflow.how_to_implement &&
                      workflow.how_to_implement.length > 0 && (
                        <div className="rounded-lg border border-edge bg-surface-alt p-5">
                          <p className="small-caps mb-3">How To Implement</p>
                          <ol className="space-y-2 text-sm leading-6 text-ink-secondary">
                            {workflow.how_to_implement.map((note, index) => (
                              <li key={note}>
                                <span className="mr-2 font-data text-ink-muted">
                                  {index + 1}.
                                </span>
                                {note}
                              </li>
                            ))}
                          </ol>
                        </div>
                      )}

                    {workflow.tradeoffs && workflow.tradeoffs.length > 0 && (
                      <div className="rounded-lg border border-edge bg-surface-alt p-5">
                        <p className="small-caps mb-3">Tradeoffs</p>
                        <ul className="space-y-2 text-sm leading-6 text-ink-secondary">
                          {workflow.tradeoffs.map((note) => (
                            <li key={note}>{note}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {workflow.citations && workflow.citations.length > 0 && (
                      <div className="rounded-lg border border-edge bg-surface-alt p-5 lg:col-span-2">
                        <p className="small-caps mb-3">Key Citations</p>
                        <ul className="space-y-3">
                          {workflow.citations.map((citation) => (
                            <li
                              key={citation.href}
                              className="text-sm leading-6 text-ink-secondary"
                            >
                              <a
                                href={citation.href}
                                target="_blank"
                                rel="noreferrer"
                                className="text-brand hover:text-accent"
                              >
                                {citation.title}
                              </a>
                              <p className="text-ink-muted">{citation.note}</p>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}
