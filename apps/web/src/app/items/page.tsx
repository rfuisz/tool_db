import { ItemsBrowseClient } from "@/components/items-browse-client";
import { getItems } from "@/lib/backend-data";

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

  return (
    <ItemsBrowseClient
      items={items}
      initialFilters={{
        type: getSingle(resolvedSearchParams.type),
        mechanism: getSingle(resolvedSearchParams.mechanism),
        technique: getSingle(resolvedSearchParams.technique),
        family: getSingle(resolvedSearchParams.family),
      }}
    />
  );
}
