"use client";

import { useI18n } from "@/components/i18n/i18n-provider";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/components/theme/theme-provider";

export function ThemeToggle() {
  const { t } = useI18n();
  const { theme, toggleTheme } = useTheme();
  const label = theme === "dark" ? t("Switch to light mode") : t("Switch to dark mode");

  return (
    <Button aria-label={label} onClick={toggleTheme} size="icon" title={label} variant="tertiary">
      {theme === "dark" ? (
        <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24"><path d="M12 4.75v-2M12 21.25v-2M19.25 12h2M2.75 12h2M17.13 6.87l1.41-1.41M4.46 19.54l1.41-1.41M17.13 17.13l1.41 1.41M4.46 4.46l1.41 1.41M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z" stroke="currentColor" strokeLinecap="round" strokeWidth="1.75" /></svg>
      ) : (
        <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24"><path d="M20.5 15.2A8.75 8.75 0 0 1 8.8 3.5 8.75 8.75 0 1 0 20.5 15.2Z" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.75" /></svg>
      )}
    </Button>
  );
}
