import Link from "next/link";
import { notFound } from "next/navigation";
import { getItemsBrowse } from "@/lib/backend-data";
import {
  ARCHITECTURE_ITEM_TYPES,
  COMPONENT_ITEM_TYPES,
} from "@/lib/item-hierarchy";
import { MECHANISM_LABELS } from "@/lib/vocabularies";
import { MECHANISM_DESCRIPTIONS } from "@/lib/explanations";
import { SearchableItemList } from "@/components/searchable-item-list";

export default async function MechanismDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  const label = MECHANISM_LABELS[slug];
  if (!label) {
    notFound();
  }

  const description =
    MECHANISM_DESCRIPTIONS[slug] ??
    "A mechanism-level grouping derived from the current toolkit evidence.";

  const result = await getItemsBrowse({
    mechanism: [slug],
    sort: "score",
    limit: 500,
    offset: 0,
  });

  const architectureItems = result.items.filter((i) =>
    (ARCHITECTURE_ITEM_TYPES as readonly string[]).includes(i.item_type),
  );
  const componentItems = result.items.filter((i) =>
    (COMPONENT_ITEM_TYPES as readonly string[]).includes(i.item_type),
  );

  return (
    <div>
      <p className="mb-8 font-ui text-sm text-ink-muted">
        <Link href="/" className="hover:text-accent">
          Home
        </Link>
        <span className="mx-2 text-ink-faint">/</span>
        <Link href="/mechanisms" className="hover:text-accent">
          Mechanisms
        </Link>
        <span className="mx-2 text-ink-faint">/</span>
        <span className="text-ink-secondary">{label}</span>
      </p>

      <header className="mb-12">
        <p className="small-caps mb-3 text-accent">Mechanism Concept</p>
        <h1 className="mb-3">{label}</h1>
        <p className="max-w-3xl text-lg leading-relaxed text-ink-secondary">
          {description}
        </p>
        <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 font-data text-sm text-ink-muted">
          <span>{result.total} total items</span>
          <span>{architectureItems.length} architectures</span>
          <span>{componentItems.length} components</span>
        </div>
        <p className="mt-6">
          <Link
            href={`/items?mechanism=${encodeURIComponent(slug)}`}
            className="small-caps text-accent hover:text-accent-hover"
          >
            Browse All Matching Toolkit Items
          </Link>
        </p>
      </header>

      <SearchableItemList title="Architectures" items={architectureItems} />
      <SearchableItemList title="Components" items={componentItems} />
    </div>
  );
}
