import { notFound } from "next/navigation";

import { FirstPassBrowseClient } from "@/components/first-pass-browse-client";
import { getFirstPassItems } from "@/lib/backend-data";
import { isFirstPassEnabled } from "@/lib/first-pass-access";

export default async function FirstPassPage() {
  if (!(await isFirstPassEnabled())) {
    notFound();
  }

  const items = await getFirstPassItems();

  return <FirstPassBrowseClient items={items} />;
}
