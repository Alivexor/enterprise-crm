import { ActivityDetail } from "@/features/activities/activity-detail";

type ActivityDetailPageProps = { params: Promise<{ activityId: string }> };

export default async function ActivityDetailPage({ params }: ActivityDetailPageProps) {
  const { activityId } = await params;
  return <ActivityDetail activityId={activityId} />;
}
