import { getItems } from "@/lib/backend-data";
import { buildTechniqueConceptSummaries } from "@/lib/item-hierarchy";
import { TechniquesBrowseClient } from "@/components/techniques-browse-client";

export default async function TechniquesPage() {
  const items = await getItems();
  const concepts = buildTechniqueConceptSummaries(items);

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
