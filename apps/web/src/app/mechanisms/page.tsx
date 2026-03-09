import Link from "next/link";
import { getItems } from "@/lib/backend-data";
import { buildMechanismConceptSummaries } from "@/lib/item-hierarchy";

export default async function MechanismsPage() {
  const items = await getItems();
  const concepts = buildMechanismConceptSummaries(items);

  return (
    <div>
      <header className="mb-12">
        <p className="small-caps mb-3 text-accent">Mechanism Index</p>
        <h1 className="mb-3">Mechanisms</h1>
        <p className="max-w-3xl text-lg leading-relaxed text-ink-secondary">
          Biophysical action modes, each summarized with the architectures,
          components, and enabled capabilities currently represented in the
          toolkit.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {concepts.map((concept) => (
          <Link
            key={concept.key}
            href={`/mechanisms/${encodeURIComponent(concept.key)}`}
            className="group rounded border border-edge p-5 transition-colors hover:border-accent"
          >
            <div className="flex items-baseline justify-between gap-3">
              <h2 className="text-xl text-ink group-hover:text-accent">
                {concept.label}
              </h2>
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
        ))}
      </div>
    </div>
  );
}
