import { apiClient } from "@/services/api-client";
import type { Note, NoteInput, NotesListParams } from "@/types/note";
import type { PaginatedResponse } from "@/types/pagination";
import { toQueryString } from "@/utils/query-string";

export const noteService = {
  create(input: NoteInput): Promise<Note> { return apiClient.post<Note>("/notes", JSON.stringify(input)); },
  get(noteId: string): Promise<Note> { return apiClient.get<Note>(`/notes/${noteId}`, { cache: "no-store" }); },
  list(params: NotesListParams = {}): Promise<PaginatedResponse<Note>> { return apiClient.get<PaginatedResponse<Note>>(`/notes${toQueryString(params)}`, { cache: "no-store" }); },
  remove(noteId: string): Promise<void> { return apiClient.delete<void>(`/notes/${noteId}`); },
  update(noteId: string, input: Partial<NoteInput>): Promise<Note> { return apiClient.patch<Note>(`/notes/${noteId}`, JSON.stringify(input)); },
};
