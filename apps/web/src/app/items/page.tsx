import { ItemsBrowseClient } from "@/components/items-browse-client";
import { getItems } from "@/lib/backend-data";
import { searchItems } from "@/lib/api-search";
import { getAllFamilies, getAllMechanisms, getAllTechniques } from "@/lib/data";

export default async function ItemsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const items = await getItems();
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

  const initialResult = searchItems(items, {
    q: "",
    type: initialFilters.type ? [initialFilters.type] : undefined,
    mechanism: initialFilters.mechanism ? [initialFilters.mechanism] : undefined,
    technique: initialFilters.technique ? [initialFilters.technique] : undefined,
    family: initialFilters.family ? [initialFilters.family] : undefined,
    sort: "score",
    limit: 50,
    offset: 0,
  });

  return (
    <ItemsBrowseClient
      allItems={items}
      initialItems={initialResult.results}
      initialTotal={initialResult.total}
      initialFilters={initialFilters}
      filterOptions={{
        types: Array.from(new Set(items.map((item) => item.item_type))).sort(),
        mechanisms: getAllMechanisms(items),
        techniques: getAllTechniques(items),
        families: getAllFamilies(items),
      }}
    />
  );
}
