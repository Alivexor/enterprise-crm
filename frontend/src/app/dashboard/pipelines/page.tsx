import { PipelinesWorkspace } from "@/features/pipelines/pipelines-workspace";

type PageProps = { searchParams: Promise<{ create?: string | string[] }> };

export default async function PipelinesPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return <PipelinesWorkspace initialCreate={params.create === "1"} />;
}
