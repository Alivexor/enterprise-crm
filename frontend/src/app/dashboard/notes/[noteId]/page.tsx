import { NoteDetail } from "@/features/notes/note-detail";

export default async function NoteDetailPage({
  params,
}: {
  params: Promise<{ noteId: string }>;
}) {
  const { noteId } = await params;
  return <NoteDetail noteId={noteId} />;
}
