import { CompaniesWorkspace } from "@/features/companies/companies-workspace";

type PageProps = { searchParams: Promise<{ create?: string | string[] }> };

export default async function CompaniesPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return <CompaniesWorkspace initialCreate={params.create === "1"} />;
}
