import Link from "next/link";
import { notFound } from "next/navigation";
import { getItems } from "@/lib/backend-data";
import { getTechniqueConceptSummary } from "@/lib/item-hierarchy";
import { renderInlineTitle } from "@/lib/render-inline-title";

export default async function TechniqueDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const items = await getItems();
  const concept = getTechniqueConceptSummary(items, slug);

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
        <Link href="/techniques" className="hover:text-accent">
          Techniques
        </Link>
        <span className="mx-2 text-ink-faint">/</span>
        <span className="text-ink-secondary">{concept.label}</span>
      </p>

      <header className="mb-12">
        <p className="small-caps mb-3 text-accent">Technique Concept</p>
        <h1 className="mb-3">{concept.label}</h1>
        <p className="max-w-3xl text-lg leading-relaxed text-ink-secondary">
          {concept.summary}
        </p>
        <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 font-data text-sm text-ink-muted">
          <span>{concept.totalCount} total methods</span>
        </div>
        {concept.capabilities.length > 0 ? (
          <p className="mt-4 font-ui text-sm text-ink-secondary">
            Main supported work: {concept.capabilities.join(", ")}.
          </p>
        ) : null}
        <p className="mt-6">
          <Link
            href={`/items?technique=${encodeURIComponent(concept.key)}`}
            className="small-caps text-accent hover:text-accent-hover"
          >
            Browse All Matching Methods
          </Link>
        </p>
      </header>

      <section className="mb-10">
        <h2 className="mb-4">Methods</h2>
        <div className="space-y-4">
          {concept.methodItems.map((item) => (
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
    </div>
  );
}
