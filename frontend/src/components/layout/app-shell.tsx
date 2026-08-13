"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import { CommandPalette } from "@/components/command/command-palette";
import { useI18n } from "@/components/i18n/i18n-provider";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";

export function AppShell({ children }: { children: ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const { isRtl, t } = useI18n();
  const closeSidebar = useCallback(() => setIsSidebarOpen(false), []);
  const openSidebar = useCallback(() => setIsSidebarOpen(true), []);
  const closeCommandPalette = useCallback(() => setIsCommandPaletteOpen(false), []);
  const openCommandPalette = useCallback(() => setIsCommandPaletteOpen(true), []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setIsCommandPaletteOpen((open) => !open);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <div className="crm-app-frame flex min-h-dvh bg-[var(--app-background)]">
      <a
        className={`fixed top-4 z-[70] -translate-y-24 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-xl transition focus:translate-y-0 focus:outline-none ${isRtl ? "right-4" : "left-4"}`}
        href="#main-content"
      >
        {t("Skip to main content")}
      </a>
      <Sidebar isOpen={isSidebarOpen} onClose={closeSidebar} />
      <div className="flex min-w-0 flex-1 flex-col lg:max-w-[calc(100vw-17.5rem)]">
        <Header onCommandClick={openCommandPalette} onMenuClick={openSidebar} />
        <main className="crm-main flex-1 px-4 py-5 focus:outline-none sm:px-6 sm:py-7 xl:px-8 xl:py-8" id="main-content" tabIndex={-1}>
          <div className="w-full">{children}</div>
        </main>
      </div>
      {isCommandPaletteOpen ? <CommandPalette onClose={closeCommandPalette} /> : null}
    </div>
  );
}
