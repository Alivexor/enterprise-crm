import { NotesWorkspace } from "@/features/notes/notes-workspace";

type PageProps = { searchParams: Promise<{ create?: string | string[] }> };

export default async function NotesPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return <NotesWorkspace initialCreate={params.create === "1"} />;
}
