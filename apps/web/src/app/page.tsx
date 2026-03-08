import Link from "next/link";
import { getItems, getWorkflows } from "@/lib/backend-data";
import { getAllFamilies, getAllMechanisms, getAllTechniques } from "@/lib/data";
import {
  ITEM_TYPE_LABELS,
  MECHANISM_LABELS,
  TECHNIQUE_LABELS,
} from "@/lib/vocabularies";
import type { ItemType } from "@/lib/types";

export default async function Home() {
  const [items, workflows] = await Promise.all([getItems(), getWorkflows()]);
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
  const mechanisms = getAllMechanisms(items);
  const techniques = getAllTechniques(items);

  return (
    <div>
      {/* Masthead */}
      <header className="mb-16 pt-8">
        <h1 className="mb-4">BioControl Toolkit DB</h1>
        <p className="max-w-xl text-lg leading-relaxed text-ink-secondary">
          An evidence-first engineering knowledge system for biological control
          surfaces, engineering methods, assay methods, and
          design&#x2013;build&#x2013;test&#x2013;learn workflows. Every claim is
          traceable to source-backed evidence.
        </p>

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
      </header>

      <hr className="mb-16" />

      {/* The Collection */}
      <section className="mb-16">
        <p className="small-caps mb-6">The Collection</p>
        <div className="grid gap-x-12 gap-y-4 sm:grid-cols-2">
          {Object.entries(typeCounts)
            .sort(([, a], [, b]) => b - a)
            .map(([type, count]) => (
              <Link
                key={type}
                href={`/items?type=${type}`}
                className="group flex items-baseline justify-between border-b border-edge py-3 transition-colors hover:border-accent"
              >
                <span className="font-display text-lg text-ink group-hover:text-accent">
                  {ITEM_TYPE_LABELS[type as ItemType]}
                </span>
                <span className="font-data text-sm tabular-nums text-ink-muted">
                  {count}
                </span>
              </Link>
            ))}
        </div>
        <p className="mt-6">
          <Link
            href="/items"
            className="small-caps text-accent hover:text-accent-hover"
          >
            Browse full collection &rarr;
          </Link>
        </p>
      </section>

      <hr className="mb-16" />

      {/* Mechanisms */}
      <section className="mb-16">
        <p className="small-caps mb-6">Explore by Mechanism</p>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          {mechanisms.map((m) => {
            const count = items.filter((i) => i.mechanisms.includes(m)).length;
            return (
              <Link
                key={m}
                href={`/items?mechanism=${m}`}
                className="group font-body text-base text-ink-secondary transition-colors hover:text-accent"
              >
                {MECHANISM_LABELS[m] ?? m.replace(/_/g, " ")}
                <sup className="ml-0.5 font-data text-xs text-ink-muted group-hover:text-accent">
                  {count}
                </sup>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Techniques */}
      <section className="mb-16">
        <p className="small-caps mb-6">Explore by Technique</p>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          {techniques.map((t) => {
            const count = items.filter((i) => i.techniques.includes(t)).length;
            return (
              <Link
                key={t}
                href={`/items?technique=${t}`}
                className="group font-body text-base text-ink-secondary transition-colors hover:text-accent"
              >
                {TECHNIQUE_LABELS[t] ?? t.replace(/_/g, " ")}
                <sup className="ml-0.5 font-data text-xs text-ink-muted group-hover:text-accent">
                  {count}
                </sup>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Families */}
      <section className="mb-16">
        <p className="small-caps mb-6">Explore by Family</p>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
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
      </section>

      <hr className="accent mb-16" />

      {/* Workflows */}
      <section className="mb-8">
        <p className="small-caps mb-6">DBTL Workflow Templates</p>
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
