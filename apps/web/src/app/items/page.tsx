import { ItemsBrowseClient } from "@/components/items-browse-client";
import { getItemsBrowse, getItemAggregates } from "@/lib/backend-data";

export default async function ItemsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const resolvedSearchParams = await searchParams;

  const getSingle = (
    value: string | string[] | undefined,
  ): string | undefined => (Array.isArray(value) ? value[0] : value);

  const initialFilters = {
    type: getSingle(resolvedSearchParams.type),
    mechanism: getSingle(resolvedSearchParams.mechanism),
    technique: getSingle(resolvedSearchParams.technique),
    family: getSingle(resolvedSearchParams.family),
  };

  const [initialResult, aggregates] = await Promise.all([
    getItemsBrowse({
      type: initialFilters.type ? [initialFilters.type] : undefined,
      mechanism: initialFilters.mechanism ? [initialFilters.mechanism] : undefined,
      technique: initialFilters.technique ? [initialFilters.technique] : undefined,
      family: initialFilters.family ? [initialFilters.family] : undefined,
      sort: "score",
      limit: 50,
      offset: 0,
    }),
    getItemAggregates(),
  ]);

  return (
    <ItemsBrowseClient
      initialItems={initialResult.items}
      initialTotal={initialResult.total}
      initialFilters={initialFilters}
      filterOptions={{
        types: aggregates.by_item_type.map((b) => b.value).sort(),
        mechanisms: aggregates.by_mechanism.map((b) => b.value).sort(),
        techniques: aggregates.by_technique.map((b) => b.value).sort(),
        families: aggregates.by_family.map((b) => b.value).sort(),
        mechanismCounts: Object.fromEntries(aggregates.by_mechanism.map((b) => [b.value, b.count])),
        techniqueCounts: Object.fromEntries(aggregates.by_technique.map((b) => [b.value, b.count])),
      }}
    />
  );
}
