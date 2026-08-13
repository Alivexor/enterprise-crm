import { LeadsWorkspace } from "@/features/leads/leads-workspace";

type PageProps = { searchParams: Promise<{ create?: string | string[] }> };

export default async function LeadsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return <LeadsWorkspace initialCreate={params.create === "1"} />;
}
