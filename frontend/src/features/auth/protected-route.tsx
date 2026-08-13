"use client";

import { useEffect, type ReactNode } from "react";
import { useI18n } from "@/components/i18n/i18n-provider";
import { useRouter } from "next/navigation";

import { useAuth } from "@/hooks/use-auth";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  const { isLoading, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user === null) {
      router.replace("/login");
    }
  }, [isLoading, router, user]);

  if (isLoading || user === null) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-[var(--app-background)]">
        <div
          aria-label={t("Checking your session")}
          className="h-7 w-7 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"
          role="status"
        />
      </div>
    );
  }

  return <>{children}</>;
}
