import { getItems } from "@/lib/backend-data";
import { buildMechanismConceptSummaries } from "@/lib/item-hierarchy";
import { MechanismsBrowseClient } from "@/components/mechanisms-browse-client";

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

      <MechanismsBrowseClient concepts={concepts} />
    </div>
  );
}
