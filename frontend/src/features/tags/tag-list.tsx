import { T } from "@/components/i18n/i18n-provider";
import { LocalizedDateTime } from "@/components/i18n/localized-value";
import Link from "next/link";

import { EmptyState } from "@/components/ui/page-state";
import type { Tag } from "@/types/tag";

export function TagList({ tags }: { tags: Tag[] }) {
  if (tags.length === 0) {
    return <EmptyState description="Create reusable labels to organize your customer records." title="No tags yet" />;
  }

  return (
    <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {tags.map((tag) => (
        <li key={tag.id}>
          <Link className="crm-card crm-card-hover block p-5 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-500" href={`/dashboard/tags/${tag.id}`}>
            <div className="flex items-center gap-3">
              <span aria-hidden="true" className="h-3.5 w-3.5 rounded-full ring-2 ring-white dark:ring-slate-950" style={{ backgroundColor: tag.color }} />
              <span className="font-semibold text-slate-900 dark:text-white">{tag.name}</span>
            </div>
            <p className="mt-4 text-xs text-slate-500"><T>Created</T> <LocalizedDateTime value={tag.created_at} /></p>
          </Link>
        </li>
      ))}
    </ul>
  );
}
