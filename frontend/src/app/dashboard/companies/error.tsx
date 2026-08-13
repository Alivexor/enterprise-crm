"use client";

import { T } from "@/components/i18n/i18n-provider";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/page-state";

type CompaniesErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function CompaniesError({ error, reset }: CompaniesErrorProps) {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") console.error("Companies page error", error);
  }, [error]);

  return (
    <ErrorState
      action={<Button onClick={reset}><T>Try again</T></Button>}
      description="We could not load the Companies workspace. Your data has not been changed."
      title="Unable to load companies"
    />
  );
}
