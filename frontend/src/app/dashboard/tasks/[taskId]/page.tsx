import { TaskDetail } from "@/features/tasks/task-detail";

type TaskDetailPageProps = { params: Promise<{ taskId: string }> };

export default async function TaskDetailPage({ params }: TaskDetailPageProps) {
  const { taskId } = await params;
  return <TaskDetail taskId={taskId} />;
}
