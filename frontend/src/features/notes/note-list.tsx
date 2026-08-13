import { LocalizedDateTime } from "@/components/i18n/localized-value";
import { T } from "@/components/i18n/i18n-provider";
import Link from "next/link";

import { EmptyState } from "@/components/ui/page-state";
import type { Note } from "@/types/note";

type NoteListProps = { companyNames: ReadonlyMap<string, string>; notes: Note[] };

export function NoteList({ companyNames, notes }: NoteListProps) {
  if (notes.length === 0) return <EmptyState description="Capture customer context, meeting outcomes, and follow-up information in a note." title="No notes yet" />;
  return <ul className="space-y-3">{notes.map((note) => <li key={note.id}><Link className="crm-card crm-card-hover block p-5 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500" href={`/dashboard/notes/${note.id}`}><p className="line-clamp-3 whitespace-pre-wrap text-sm leading-6 text-slate-800 dark:text-slate-100">{note.content}</p><div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500"><span><LocalizedDateTime value={note.updated_at} /></span>{note.company_id ? <span>{companyNames.get(note.company_id) ?? <T>Unknown company</T>}</span> : <span><T>General note</T></span>}</div></Link></li>)}</ul>;
}
