"use client";

import { T } from "@/components/i18n/i18n-provider";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/page-state";

type ErrorPageProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") console.error("Unhandled application error", error);
  }, [error]);

  return (
    <main className="mx-auto flex min-h-dvh max-w-xl items-center px-4 py-6 sm:px-6">
      <ErrorState
        action={<Button onClick={reset}><T>Try again</T></Button>}
        description="We could not load this part of Enterprise CRM. Your data has not been changed."
        title="Something went wrong"
      />
    </main>
  );
}
