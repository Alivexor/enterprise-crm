import { ActivitiesWorkspace } from "@/features/activities/activities-workspace";

type PageProps = { searchParams: Promise<{ create?: string | string[] }> };

export default async function ActivitiesPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return <ActivitiesWorkspace initialCreate={params.create === "1"} />;
}
