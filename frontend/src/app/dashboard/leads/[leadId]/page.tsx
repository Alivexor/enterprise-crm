import { LeadDetail } from "@/features/leads/lead-detail";

type LeadDetailPageProps = { params: Promise<{ leadId: string }> };

export default async function LeadDetailPage({ params }: LeadDetailPageProps) {
  const { leadId } = await params;
  return <LeadDetail leadId={leadId} />;
}
