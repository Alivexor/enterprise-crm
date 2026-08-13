import { DealsWorkspace } from "@/features/deals/deals-workspace";

type PageProps = { searchParams: Promise<{ create?: string | string[] }> };

export default async function DealsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return <DealsWorkspace initialCreate={params.create === "1"} />;
}
