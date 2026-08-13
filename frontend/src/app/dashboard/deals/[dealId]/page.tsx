import { DealDetail } from "@/features/deals/deal-detail";

type DealDetailPageProps = { params: Promise<{ dealId: string }> };

export default async function DealDetailPage({ params }: DealDetailPageProps) {
  const { dealId } = await params;
  return <DealDetail dealId={dealId} />;
}
