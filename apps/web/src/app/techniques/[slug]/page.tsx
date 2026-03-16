import Link from "next/link";
import { notFound } from "next/navigation";
import { getItemsBrowse } from "@/lib/backend-data";
import { TECHNIQUE_LABELS } from "@/lib/vocabularies";
import { TECHNIQUE_DESCRIPTIONS } from "@/lib/explanations";
import { SearchableItemList } from "@/components/searchable-item-list";

export default async function TechniqueDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  const label = TECHNIQUE_LABELS[slug];
  if (!label) {
    notFound();
  }

  const description =
    TECHNIQUE_DESCRIPTIONS[slug] ??
    "A technique-level grouping derived from the current toolkit evidence.";

  const result = await getItemsBrowse({
    technique: [slug],
    sort: "score",
    limit: 500,
    offset: 0,
  });

  return (
    <div>
      <p className="mb-8 font-ui text-sm text-ink-muted">
        <Link href="/" className="hover:text-accent">
          Home
        </Link>
        <span className="mx-2 text-ink-faint">/</span>
        <Link href="/techniques" className="hover:text-accent">
          Techniques
        </Link>
        <span className="mx-2 text-ink-faint">/</span>
        <span className="text-ink-secondary">{label}</span>
      </p>

      <header className="mb-12">
        <p className="small-caps mb-3 text-accent">Technique Concept</p>
        <h1 className="mb-3">{label}</h1>
        <p className="max-w-3xl text-lg leading-relaxed text-ink-secondary">
          {description}
        </p>
        <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 font-data text-sm text-ink-muted">
          <span>{result.total} total methods</span>
        </div>
        <p className="mt-6">
          <Link
            href={`/items?technique=${encodeURIComponent(slug)}`}
            className="small-caps text-accent hover:text-accent-hover"
          >
            Browse All Matching Methods
          </Link>
        </p>
      </header>

      <SearchableItemList title="Methods" items={result.items} />
    </div>
  );
}
