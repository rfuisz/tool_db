import Link from "next/link";
import { LocalRenderSyncButton } from "@/components/local-render-sync-button";
import { isLocalAdminEnabled } from "@/lib/first-pass-access";
import { getItems, getWorkflows } from "@/lib/backend-data";
import { getAllFamilies } from "@/lib/data";
import {
  MECHANISM_HIERARCHY_SECTIONS,
  buildMechanismConceptSummaries,
  buildTechniqueConceptSummaries,
  getItemTypeCount,
  getOrderedItemTypes,
  TECHNIQUE_HIERARCHY_SECTIONS,
} from "@/lib/item-hierarchy";
import {
  ITEM_TYPE_LABELS,
  MECHANISM_LABELS,
  TECHNIQUE_LABELS,
} from "@/lib/vocabularies";
import type { ItemType } from "@/lib/types";

export default async function Home() {
  const [items, workflows] = await Promise.all([getItems(), getWorkflows()]);
  const showLocalAdmin = await isLocalAdminEnabled();
  const typeCounts = items.reduce<Record<string, number>>((acc, item) => {
    acc[item.item_type] = (acc[item.item_type] || 0) + 1;
    return acc;
  }, {});

  const withReplication = items.filter(
    (i) => i.replication_summary && !i.replication_summary.orphan_tool_flag,
  );
  const avgEvidence = withReplication.length
    ? withReplication.reduce(
        (s, i) => s + (i.replication_summary?.evidence_strength_score ?? 0),
        0,
      ) / withReplication.length
    : null;

  const families = getAllFamilies(items);
  const mechanismConcepts = buildMechanismConceptSummaries(items);
  const techniqueConcepts = buildTechniqueConceptSummaries(items);

  return (
    <div>
      {/* Masthead */}
      <header className="mb-16 pt-8">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:items-start">
          <blockquote className="order-2 border-l-2 border-accent/30 pl-5 text-[22px] leading-relaxed text-ink lg:order-1">
            <p className="whitespace-pre-line">
              {`I live my life in circles that grow wide
And endlessly unroll,
I may not reach the last, but on I glide
Strong pinioned toward my goal.

About the old tower, dark against the sky,
The beat of my wings hums,
I circle about God, sweep far and high
On through milleniums.

Am I a bird that skims the clouds along,
Or am I a wild storm, or a great song?`}
            </p>
            <p className="mt-3 font-ui text-sm tracking-wide text-ink-muted not-italic">
              Rainer Maria Rilke,{" "}
              <span className="italic">The Book of a Monk&apos;s Life</span>
            </p>
          </blockquote>

          <div className="order-1 lg:order-2">
            <p className="small-caps mb-4 text-accent">
              Evidence-first engineering knowledge system
            </p>
            <p className="max-w-2xl text-lg leading-relaxed text-ink-secondary">
              A structured reference for mechanisms, architectures, components,
              methods, and design&#x2013;build&#x2013;test&#x2013;learn
              workflows, built so every claim remains traceable to source-backed
              evidence.
            </p>
          </div>
        </div>

        {/* Stats as a quiet data line */}
        <div className="mt-8 flex flex-wrap gap-x-8 gap-y-2 font-data text-sm tracking-wide text-ink-muted">
          <span>
            <strong className="text-ink">{items.length}</strong> items
          </span>
          <span>
            <strong className="text-ink">{families.length}</strong> families
          </span>
          <span>
            <strong className="text-ink">{workflows.length}</strong> workflows
          </span>
          {avgEvidence !== null && (
            <span>
              <strong className="text-ink">
                {Math.round(avgEvidence * 100)}
              </strong>{" "}
              avg evidence score
            </span>
          )}
          {items.some((i) => i.status === "seed") && (
            <span className="text-caution">
              seed data &mdash; curation in progress
            </span>
          )}
        </div>
        {showLocalAdmin && <LocalRenderSyncButton />}
      </header>

      <hr className="mb-16" />

      {/* Toolkit model */}
      <section className="mb-16">
        <p className="small-caps mb-4">Toolkit Model</p>
        <p className="mb-8 max-w-3xl text-[15px] leading-relaxed text-ink-secondary">
          The collection is best read as two hierarchies beneath workflows:
          mechanisms and techniques. Within mechanisms, the hierarchy runs from
          mechanism to architecture to component. Within techniques, the
          hierarchy runs from technique to method.
        </p>
        <div className="grid gap-8 lg:grid-cols-2">
          <div className="border border-edge p-5">
            <p className="small-caps mb-3 text-accent">Mechanism Branch</p>
            <div className="space-y-6">
              {MECHANISM_HIERARCHY_SECTIONS.map((section, index) => (
                <div key={section.id}>
                  <p className="small-caps mb-2 text-ink-muted">
                    Layer {index + 1}
                  </p>
                  <h3 className="mb-2">{section.title}</h3>
                  <p className="mb-3 text-sm leading-relaxed text-ink-secondary">
                    {section.description}
                  </p>
                  {section.id === "mechanism" ? (
                    <div className="grid gap-3 md:grid-cols-2">
                      {mechanismConcepts.map((concept) => {
                        return (
                          <Link
                            key={concept.key}
                            href={`/mechanisms/${concept.key}`}
                            className="group rounded border border-edge p-4 transition-colors hover:border-accent"
                          >
                            <div className="flex items-baseline justify-between gap-3">
                              <span className="font-display text-lg text-ink group-hover:text-accent">
                                {MECHANISM_LABELS[concept.key] ?? concept.label}
                              </span>
                              <span className="font-data text-xs text-ink-muted">
                                {concept.totalCount}
                              </span>
                            </div>
                            <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
                              {concept.summary}
                            </p>
                            <p className="mt-3 font-ui text-xs text-ink-muted">
                              {concept.architectureCount} architectures ·{" "}
                              {concept.componentCount} components
                            </p>
                          </Link>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {getOrderedItemTypes(section.itemTypes ?? [])
                        .filter((type) => typeCounts[type] > 0)
                        .map((type) => (
                          <Link
                            key={type}
                            href={`/items?type=${type}`}
                            className="group flex items-baseline justify-between border-b border-edge py-2 transition-colors hover:border-accent"
                          >
                            <span className="font-display text-lg text-ink group-hover:text-accent">
                              {ITEM_TYPE_LABELS[type as ItemType]}
                            </span>
                            <span className="font-data text-sm tabular-nums text-ink-muted">
                              {getItemTypeCount(items, type)}
                            </span>
                          </Link>
                        ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="border border-edge p-5">
            <p className="small-caps mb-3 text-accent">Technique Branch</p>
            <div className="space-y-6">
              {TECHNIQUE_HIERARCHY_SECTIONS.map((section, index) => (
                <div key={section.id}>
                  <p className="small-caps mb-2 text-ink-muted">
                    Layer {index + 1}
                  </p>
                  <h3 className="mb-2">{section.title}</h3>
                  <p className="mb-3 text-sm leading-relaxed text-ink-secondary">
                    {section.description}
                  </p>
                  {section.id === "technique" ? (
                    <div className="grid gap-3 md:grid-cols-2">
                      {techniqueConcepts.map((concept) => {
                        return (
                          <Link
                            key={concept.key}
                            href={`/techniques/${concept.key}`}
                            className="group rounded border border-edge p-4 transition-colors hover:border-accent"
                          >
                            <div className="flex items-baseline justify-between gap-3">
                              <span className="font-display text-lg text-ink group-hover:text-accent">
                                {TECHNIQUE_LABELS[concept.key] ?? concept.label}
                              </span>
                              <span className="font-data text-xs text-ink-muted">
                                {concept.totalCount}
                              </span>
                            </div>
                            <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
                              {concept.summary}
                            </p>
                            <p className="mt-3 font-ui text-xs text-ink-muted">
                              {concept.methodCount} methods
                            </p>
                          </Link>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {getOrderedItemTypes(section.itemTypes ?? [])
                        .filter((type) => typeCounts[type] > 0)
                        .map((type) => (
                          <Link
                            key={type}
                            href={`/items?type=${type}`}
                            className="group flex items-baseline justify-between border-b border-edge py-2 transition-colors hover:border-accent"
                          >
                            <span className="font-display text-lg text-ink group-hover:text-accent">
                              {ITEM_TYPE_LABELS[type as ItemType]}
                            </span>
                            <span className="font-data text-sm tabular-nums text-ink-muted">
                              {getItemTypeCount(items, type)}
                            </span>
                          </Link>
                        ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-ink-secondary">
          Families remain a useful supporting lens for browsing related lineages
          like LOV, BLUF, phytochromes, or display platforms, but they are not
          the top conceptual hierarchy.
        </p>
        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2">
          {families.map((f) => {
            const count = items.filter((i) => i.family === f).length;
            return (
              <Link
                key={f}
                href={`/items?family=${f}`}
                className="group font-body text-base text-ink-secondary transition-colors hover:text-accent"
              >
                {f}
                <sup className="ml-0.5 font-data text-xs text-ink-muted group-hover:text-accent">
                  {count}
                </sup>
              </Link>
            );
          })}
        </div>
        <p className="mt-6">
          <Link
            href="/items"
            className="small-caps text-accent hover:text-accent-hover"
          >
            Browse toolkit items &rarr;
          </Link>
        </p>
      </section>

      <hr className="accent mb-16" />

      {/* Workflows */}
      <section className="mb-8">
        <p className="small-caps mb-4">Workflow Layer</p>
        <p className="mb-6 max-w-3xl text-[15px] leading-relaxed text-ink-secondary">
          Workflows sit above both branches. They combine mechanisms and
          techniques to obtain, optimize, verify, characterize, deliver, and
          evaluate engineered systems.
        </p>
        <div className="space-y-8">
          {workflows.map((w) => {
            const totalDays = Math.round(
              w.steps.reduce(
                (s, st) => s + (st.duration_typical_hours ?? 0),
                0,
              ) / 24,
            );
            const totalCost = w.steps.reduce(
              (s, st) => s + (st.direct_cost_usd_typical ?? 0),
              0,
            );
            return (
              <Link
                key={w.id}
                href={`/workflows#${w.slug}`}
                className="group block border-b border-edge pb-8 transition-colors hover:border-accent"
              >
                <h3 className="mb-1 text-ink group-hover:text-accent">
                  {w.name}
                </h3>
                <p className="mb-2 text-[15px] text-ink-secondary">
                  {w.objective}
                </p>
                <span className="font-data text-sm text-ink-muted">
                  {w.steps.length} steps &middot; ~{totalDays}d &middot; $
                  {totalCost.toLocaleString()}
                </span>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
