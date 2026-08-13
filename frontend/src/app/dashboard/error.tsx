"use client";

import { T } from "@/components/i18n/i18n-provider";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/page-state";

type DashboardErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function DashboardError({ error, reset }: DashboardErrorProps) {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") console.error("Dashboard error", error);
  }, [error]);

  return (
    <ErrorState
      action={<Button onClick={reset}><T>Try again</T></Button>}
      description="We could not load this workspace view. Your data has not been changed."
      title="Unable to load this page"
    />
  );
}
