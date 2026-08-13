import { CompanyDetail } from "@/features/companies/company-detail";

type CompanyDetailPageProps = {
  params: Promise<{ companyId: string }>;
};

export default async function CompanyDetailPage({
  params,
}: CompanyDetailPageProps) {
  const { companyId } = await params;
  return <CompanyDetail companyId={companyId} />;
}
