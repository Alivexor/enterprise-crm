import { TasksWorkspace } from "@/features/tasks/tasks-workspace";

type PageProps = { searchParams: Promise<{ create?: string | string[] }> };

export default async function TasksPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return <TasksWorkspace initialCreate={params.create === "1"} />;
}
