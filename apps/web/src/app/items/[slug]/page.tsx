import { notFound } from "next/navigation";
import Link from "next/link";
import { ITEMS } from "@/lib/data";
import {
  ITEM_TYPE_LABELS,
  MATURITY_LABELS,
  MODALITY_LABELS,
  BIO_SYSTEM_LABELS,
} from "@/lib/vocabularies";
import { ScoreBreakdown } from "@/components/score-bar";
import { ValidationMatrix } from "@/components/validation-dots";
import { CitationList } from "@/components/citation-list";
import type { ValidationObservation } from "@/lib/types";

export function generateStaticParams() {
  return ITEMS.map((item) => ({ slug: item.slug }));
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-12">
      <p className="small-caps mb-4">{title}</p>
      {children}
    </section>
  );
}

function ObservationRow({ obs }: { obs: ValidationObservation }) {
  const outcomeColor =
    obs.success_outcome === "success"
      ? "text-valid"
      : obs.success_outcome === "mixed"
        ? "text-caution"
        : "text-danger";

  return (
    <div className="border-b border-edge py-4 last:border-b-0">
      <div className="mb-1 flex flex-wrap items-baseline gap-x-3 gap-y-1 font-ui text-sm">
        <span className={`font-semibold ${outcomeColor}`}>
          {obs.success_outcome}
        </span>
        <span className="text-ink-secondary">
          {BIO_SYSTEM_LABELS[obs.biological_system_level]}
        </span>
        <span className="text-ink-muted">
          {obs.observation_type.replace(/_/g, " ")}
        </span>
        {obs.species && <span className="italic text-ink-muted">{obs.species}</span>}
        {obs.cell_type && <span className="text-ink-muted">{obs.cell_type}</span>}
        {obs.independent_lab_cluster_id && (
          <span className="text-brand">independent</span>
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
          {obs.metrics.map((m, i) => (
            <span key={i} className="text-ink-secondary">
              <span className="text-ink-muted">{m.metric_name.replace(/_/g, " ")}</span>
              {m.value_num !== null && (
                <span className="ml-1.5 text-ink">
                  {m.value_num}{m.unit && ` ${m.unit}`}
                </span>
              )}
              {m.qualifier && <span className="ml-1 text-ink-muted">({m.qualifier})</span>}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default async function ItemDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const item = ITEMS.find((i) => i.slug === slug);
  if (!item) notFound();

  const rep = item.replication_summary;

  return (
    <div>
      {/* Breadcrumb */}
      <p className="mb-8 font-ui text-sm text-ink-muted">
        <Link href="/items" className="hover:text-accent">Collection</Link>
        <span className="mx-2 text-ink-faint">/</span>
        <span className="text-ink-secondary">{item.canonical_name}</span>
      </p>

      {/* Header */}
      <header className="mb-12">
        <h1 className="mb-3">{item.canonical_name}</h1>
        <p className="font-ui text-sm text-ink-muted">
          {ITEM_TYPE_LABELS[item.item_type]}
          {item.family && <> &middot; {item.family}</>}
          {" "}&middot; {MATURITY_LABELS[item.maturity_stage]}
          {item.first_publication_year && <> &middot; Since {item.first_publication_year}</>}
          {item.status === "seed" && (
            <span className="ml-2 text-caution">Seed — needs curation</span>
          )}
        </p>
        {item.synonyms.length > 0 && (
          <p className="mt-1 font-ui text-sm italic text-ink-faint">
            Also known as: {item.synonyms.join(", ")}
          </p>
        )}
      </header>

      <div className="grid gap-16 lg:grid-cols-[1fr_280px]">
        {/* Main column */}
        <div>
          {/* Summary */}
          <Section title="Summary">
            <p className="text-lg leading-relaxed text-ink-secondary">
              {item.summary ?? "No summary available."}
            </p>
          </Section>

          {/* Mechanism, Technique & Modality */}
          <Section title="Mechanism, Technique & Modality">
            <div className="grid gap-6 font-ui text-sm sm:grid-cols-3">
              {item.mechanisms.length > 0 && (
                <div>
                  <p className="mb-1 text-xs text-ink-muted">Mechanisms</p>
                  {item.mechanisms.map((m) => (
                    <Link
                      key={m}
                      href={`/items?mechanism=${m}`}
                      className="mr-2 text-ink-secondary hover:text-accent"
                    >
                      {m.replace(/_/g, " ")}
                    </Link>
                  ))}
                </div>
              )}
              {item.techniques.length > 0 && (
                <div>
                  <p className="mb-1 text-xs text-ink-muted">Techniques</p>
                  {item.techniques.map((t) => (
                    <Link
                      key={t}
                      href={`/items?technique=${t}`}
                      className="mr-2 text-ink-secondary hover:text-accent"
                    >
                      {t.replace(/_/g, " ")}
                    </Link>
                  ))}
                </div>
              )}
              <div>
                <p className="mb-1 text-xs text-ink-muted">Target processes</p>
                {item.target_processes.map((p) => (
                  <span key={p} className="mr-2 text-ink-secondary">{p}</span>
                ))}
              </div>
              <div>
                {item.primary_input_modality && (
                  <p className="text-ink-secondary">
                    <span className="text-xs text-ink-muted">Input: </span>
                    {MODALITY_LABELS[item.primary_input_modality]}
                  </p>
                )}
                {item.primary_output_modality && (
                  <p className="text-ink-secondary">
                    <span className="text-xs text-ink-muted">Output: </span>
                    {MODALITY_LABELS[item.primary_output_modality]}
                  </p>
                )}
              </div>
            </div>
          </Section>

          {/* Validation Matrix */}
          {item.validation_rollup && (
            <Section title="Validation">
              <ValidationMatrix rollup={item.validation_rollup} />
            </Section>
          )}

          {/* Validation Observations */}
          {item.validations.length > 0 && (
            <Section title="Observations">
              <div>
                {item.validations.map((obs) => (
                  <ObservationRow key={obs.id} obs={obs} />
                ))}
              </div>
            </Section>
          )}

          {/* Citations */}
          <Section title="Ranked Citations">
            {item.citations.length > 0 ? (
              <CitationList citations={item.citations} />
            ) : (
              <p className="font-ui text-sm italic text-ink-muted">
                No citations yet. This item needs source-backed curation.
              </p>
            )}
          </Section>

          {/* Curation status */}
          {item.status === "seed" && (
            <Section title="Curation Status">
              <div className="rounded border border-caution-light bg-caution-light/30 px-5 py-4 font-ui text-sm text-caution">
                <p className="mb-2 font-semibold">Seed dossier &mdash; not yet curator-complete</p>
                <ul className="list-inside list-disc space-y-1 text-ink-secondary">
                  <li>Validation rollups and replication scores are pending ingestion</li>
                  <li>Citation list may be incomplete or contain placeholders</li>
                  <li>Observation table will populate once evidence is curated</li>
                </ul>
              </div>
            </Section>
          )}
        </div>

        {/* Sidebar */}
        <aside className="space-y-8">
          {rep ? (
            <>
              {/* Scores */}
              <div>
                <p className="small-caps mb-4">Scores</p>
                <ScoreBreakdown
                  scores={[
                    { label: "Evidence", value: rep.evidence_strength_score },
                    { label: "Replication", value: rep.replication_score },
                    { label: "Practicality", value: rep.practicality_score },
                    { label: "Translatability", value: rep.translatability_score },
                  ]}
                />
                <p className="mt-3 font-data text-[10px] text-ink-faint">
                  v{rep.score_version}
                </p>
              </div>

              <hr />

              {/* Replication Stats */}
              <div>
                <p className="small-caps mb-4">Replication</p>
                <dl className="space-y-2 font-ui text-sm">
                  {([
                    ["Papers", rep.primary_paper_count],
                    ["Independent", rep.independent_primary_paper_count],
                    ["Author clusters", rep.distinct_last_author_clusters],
                    ["Institutions", rep.distinct_institutions],
                    ["Bio contexts", rep.distinct_biological_contexts],
                    ["Years", rep.years_since_first_report ?? "\u2014"],
                    ["Applications", rep.downstream_application_count],
                  ] as [string, string | number][]).map(([label, value]) => (
                    <div key={label} className="flex justify-between">
                      <dt className="text-ink-muted">{label}</dt>
                      <dd className="font-data tabular-nums text-ink">{String(value)}</dd>
                    </div>
                  ))}
                  {rep.orphan_tool_flag && (
                    <p className="mt-2 text-sm text-danger">
                      Orphan tool &mdash; limited independent reuse
                    </p>
                  )}
                </dl>
              </div>

              {/* Practicality Penalties */}
              {rep.practicality_penalties.length > 0 && (
                <>
                  <hr />
                  <div>
                    <p className="small-caps mb-3 text-caution">Penalties</p>
                    <ul className="space-y-2">
                      {rep.practicality_penalties.map((p, i) => (
                        <li key={i} className="flex gap-2 text-sm text-caution">
                          <span className="shrink-0">&bull;</span>
                          <span className="font-body">{p}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </>
              )}
            </>
          ) : (
            <div>
              <p className="small-caps mb-4">Scores</p>
              <p className="font-ui text-sm italic text-ink-muted">
                Scores not yet computed. Replication and evidence metrics
                will appear once citation-graph ingestion is complete.
              </p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
