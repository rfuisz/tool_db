"use client";

import type { ValidationObservation } from "@/lib/types";
import { BIO_SYSTEM_LABELS } from "@/lib/vocabularies";
import { Tooltip } from "./tooltip";
import {
  BIO_SYSTEM_DESCRIPTIONS,
  OBSERVATION_TYPE_DESCRIPTIONS,
  SUCCESS_OUTCOME_DESCRIPTIONS,
  METRIC_DESCRIPTIONS,
} from "@/lib/explanations";

export function ObservationRow({ obs }: { obs: ValidationObservation }) {
  const outcomeColor =
    obs.success_outcome === "success"
      ? "text-valid"
      : obs.success_outcome === "mixed"
        ? "text-caution"
        : "text-danger";

  return (
    <div className="border-b border-edge py-4 last:border-b-0">
      <div className="mb-1 flex flex-wrap items-baseline gap-x-3 gap-y-1 font-ui text-sm">
        <Tooltip
          content={SUCCESS_OUTCOME_DESCRIPTIONS[obs.success_outcome] ?? obs.success_outcome}
          position="bottom"
        >
          <span className={`cursor-help font-semibold ${outcomeColor}`}>
            {obs.success_outcome}
          </span>
        </Tooltip>
        <Tooltip
          content={BIO_SYSTEM_DESCRIPTIONS[obs.biological_system_level] ?? obs.biological_system_level}
          position="bottom"
        >
          <span className="cursor-help border-b border-dotted border-ink-faint text-ink-secondary">
            {BIO_SYSTEM_LABELS[obs.biological_system_level]}
          </span>
        </Tooltip>
        <Tooltip
          content={OBSERVATION_TYPE_DESCRIPTIONS[obs.observation_type] ?? obs.observation_type}
          position="bottom"
        >
          <span className="cursor-help border-b border-dotted border-ink-faint text-ink-muted">
            {obs.observation_type.replace(/_/g, " ")}
          </span>
        </Tooltip>
        {obs.species && <span className="italic text-ink-muted">{obs.species}</span>}
        {obs.cell_type && <span className="text-ink-muted">{obs.cell_type}</span>}
        {obs.independent_lab_cluster_id && (
          <Tooltip content="This observation comes from a lab unaffiliated with the original authors" position="bottom">
            <span className="cursor-help text-brand">independent</span>
          </Tooltip>
        )}
      </div>

      {obs.construct_name && (
        <p className="mb-0.5 font-ui text-sm text-ink-secondary">
          Construct: <span className="font-data">{obs.construct_name}</span>
        </p>
      )}

      {obs.assay_description && (
        <p className="text-sm text-ink-muted">{obs.assay_description}</p>
      )}

      {obs.metrics.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 font-data text-sm">
          {obs.metrics.map((m, i) => {
            const metricDesc = METRIC_DESCRIPTIONS[m.metric_name];
            return (
              <span key={i} className="text-ink-secondary">
                {metricDesc ? (
                  <Tooltip content={metricDesc} position="top">
                    <span className="cursor-help border-b border-dotted border-ink-faint text-ink-muted">
                      {m.metric_name.replace(/_/g, " ")}
                    </span>
                  </Tooltip>
                ) : (
                  <span className="text-ink-muted">{m.metric_name.replace(/_/g, " ")}</span>
                )}
                {m.value_num !== null && (
                  <span className="ml-1.5 text-ink">
                    {m.value_num}{m.unit && ` ${m.unit}`}
                  </span>
                )}
                {m.qualifier && <span className="ml-1 text-ink-muted">({m.qualifier})</span>}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
