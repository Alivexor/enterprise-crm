import { PipelineDetail } from "@/features/pipelines/pipeline-detail";

type PipelineDetailPageProps = { params: Promise<{ pipelineId: string }> };

export default async function PipelineDetailPage({ params }: PipelineDetailPageProps) {
  const { pipelineId } = await params;
  return <PipelineDetail pipelineId={pipelineId} />;
}
