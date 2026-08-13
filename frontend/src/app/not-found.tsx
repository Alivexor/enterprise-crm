import Link from "next/link";
import { T } from "@/components/i18n/i18n-provider";

import { EmptyState } from "@/components/ui/page-state";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-xl items-center px-4 py-6 sm:px-6">
      <EmptyState
        action={
          <Link
            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:focus-visible:ring-indigo-950"
            href="/dashboard"
          >
            <T>Return to dashboard</T>
          </Link>
        }
        description="The page you requested does not exist or is no longer available."
        title="Page not found"
      />
    </main>
  );
}
