import { getItemAggregates } from "@/lib/backend-data";
import { TECHNIQUE_LABELS } from "@/lib/vocabularies";
import { TECHNIQUE_DESCRIPTIONS } from "@/lib/explanations";
import { TechniquesBrowseClient } from "@/components/techniques-browse-client";

export default async function TechniquesPage() {
  const aggregates = await getItemAggregates();

  const concepts = aggregates.by_technique
    .map((b) => ({
      key: b.value,
      label: TECHNIQUE_LABELS[b.value] ?? b.value.replace(/_/g, " "),
      description:
        TECHNIQUE_DESCRIPTIONS[b.value] ??
        "A technique-level grouping derived from the current toolkit evidence.",
      totalCount: b.count,
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

  return (
    <div>
      <header className="mb-12">
        <p className="small-caps mb-3 text-accent">Technique Index</p>
        <h1 className="mb-3">Techniques</h1>
        <p className="max-w-3xl text-lg leading-relaxed text-ink-secondary">
          Practice-oriented engineering approaches, each summarized with the
          concrete methods currently available in the toolkit.
        </p>
      </header>

      <TechniquesBrowseClient concepts={concepts} />
    </div>
  );
}
