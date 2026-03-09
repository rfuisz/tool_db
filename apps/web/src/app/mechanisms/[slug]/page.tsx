import Link from "next/link";
import { notFound } from "next/navigation";
import { getItems } from "@/lib/backend-data";
import { getMechanismConceptSummary } from "@/lib/item-hierarchy";
import { renderInlineTitle } from "@/lib/render-inline-title";

function ItemList({
  title,
  items,
}: {
  title: string;
  items: Array<{
    slug: string;
    canonical_name: string;
    summary: string | null;
  }>;
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="mb-10">
      <h2 className="mb-4">{title}</h2>
      <div className="space-y-4">
        {items.map((item) => (
          <article key={item.slug} className="border border-edge p-5">
            <Link
              href={`/items/${item.slug}`}
              className="text-lg text-brand hover:text-accent"
            >
              {renderInlineTitle(item.canonical_name)}
            </Link>
            {item.summary ? (
              <p className="mt-2 text-sm leading-relaxed text-ink-secondary">
                {renderInlineTitle(item.summary)}
              </p>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

export default async function MechanismDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const items = await getItems();
  const concept = getMechanismConceptSummary(items, slug);

  if (!concept) {
    notFound();
  }

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
        <span className="text-ink-secondary">{concept.label}</span>
      </p>

      <header className="mb-12">
        <p className="small-caps mb-3 text-accent">Mechanism Concept</p>
        <h1 className="mb-3">{concept.label}</h1>
        <p className="max-w-3xl text-lg leading-relaxed text-ink-secondary">
          {concept.summary}
        </p>
        <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 font-data text-sm text-ink-muted">
          <span>{concept.totalCount} total items</span>
          <span>{concept.architectureCount} architectures</span>
          <span>{concept.componentCount} components</span>
        </div>
        {concept.capabilities.length > 0 ? (
          <p className="mt-4 font-ui text-sm text-ink-secondary">
            Main enabled capabilities: {concept.capabilities.join(", ")}.
          </p>
        ) : null}
        <p className="mt-6">
          <Link
            href={`/items?mechanism=${encodeURIComponent(concept.key)}`}
            className="small-caps text-accent hover:text-accent-hover"
          >
            Browse All Matching Toolkit Items
          </Link>
        </p>
      </header>

      <ItemList title="Architectures" items={concept.architectureItems} />
      <ItemList title="Components" items={concept.componentItems} />
    </div>
  );
}
