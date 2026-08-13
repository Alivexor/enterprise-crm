"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/i18n/i18n-provider";
import { notificationService } from "@/services/notification-service";
import { NOTIFICATIONS_CHANGED_EVENT } from "@/utils/notification-events";

export function NotificationBell() {
  const { formatNumber, locale, t } = useI18n();
  const [unreadCount, setUnreadCount] = useState<number | null>(null);

  useEffect(() => {
    let isActive = true;

    async function loadUnreadCount() {
      try {
        const response = await notificationService.list({ page: 1, page_size: 1, read: "unread" });
        if (isActive) setUnreadCount(response.meta.total);
      } catch {
        if (isActive) setUnreadCount(null);
      }
    }

    function handleVisibility() {
      if (document.visibilityState === "visible") void loadUnreadCount();
    }

    void loadUnreadCount();
    const intervalId = window.setInterval(() => {
      if (document.visibilityState === "visible") void loadUnreadCount();
    }, 60_000);
    window.addEventListener(NOTIFICATIONS_CHANGED_EVENT, loadUnreadCount);
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      isActive = false;
      window.clearInterval(intervalId);
      window.removeEventListener(NOTIFICATIONS_CHANGED_EVENT, loadUnreadCount);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, []);

  const visibleCount = unreadCount && unreadCount > 99 ? "99+" : unreadCount;
  const label = unreadCount === null
    ? t("Open notifications")
    : locale === "fa"
      ? `باز کردن اعلان‌ها${unreadCount > 0 ? ` (${formatNumber(unreadCount)} خوانده‌نشده)` : ""}`
      : `Open notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ""}`;

  return (
    <Link aria-label={label} className="relative inline-flex h-10 w-10 items-center justify-center rounded-xl border border-transparent text-slate-500 transition-[color,background-color,border-color,box-shadow,transform] duration-200 hover:border-slate-200/80 hover:bg-white hover:text-slate-950 hover:shadow-sm focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-indigo-200 dark:text-slate-300 dark:hover:border-slate-800 dark:hover:bg-slate-900 dark:hover:text-white dark:focus-visible:ring-indigo-950" href="/dashboard/notifications">
      <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24"><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" /></svg>
      {typeof visibleCount === "number" || typeof visibleCount === "string" ? <span aria-hidden="true" className="absolute -end-0.5 -top-0.5 min-w-4 rounded-full border-2 border-white bg-rose-500 px-1 text-center text-[9px] font-extrabold leading-3.5 text-white shadow-sm dark:border-slate-950">{typeof visibleCount === "number" ? formatNumber(visibleCount) : visibleCount}</span> : null}
    </Link>
  );
}
