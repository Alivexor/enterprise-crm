import { TagDetail } from "@/features/tags/tag-detail";

export default async function TagDetailPage({
  params,
}: {
  params: Promise<{ tagId: string }>;
}) {
  const { tagId } = await params;
  return <TagDetail tagId={tagId} />;
}
