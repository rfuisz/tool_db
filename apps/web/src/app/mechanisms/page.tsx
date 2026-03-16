import { getItemAggregates } from "@/lib/backend-data";
import { MECHANISM_LABELS } from "@/lib/vocabularies";
import { MECHANISM_DESCRIPTIONS } from "@/lib/explanations";
import { MechanismsBrowseClient } from "@/components/mechanisms-browse-client";

export default async function MechanismsPage() {
  const aggregates = await getItemAggregates();

  const concepts = aggregates.by_mechanism
    .map((b) => ({
      key: b.value,
      label: MECHANISM_LABELS[b.value] ?? b.value.replace(/_/g, " "),
      description:
        MECHANISM_DESCRIPTIONS[b.value] ??
        "A mechanism-level grouping derived from the current toolkit evidence.",
      totalCount: b.count,
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

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

      <MechanismsBrowseClient concepts={concepts} />
    </div>
  );
}
