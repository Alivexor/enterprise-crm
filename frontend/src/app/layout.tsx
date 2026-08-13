import type { Metadata } from "next";
import type { ReactNode } from "react";
import Script from "next/script";
import { ThemeProvider, themeBootstrapScript } from "@/components/theme/theme-provider";
import { I18nProvider, localeBootstrapScript } from "@/components/i18n/i18n-provider";
import { AuthProvider } from "@/features/auth/auth-provider";
import { ToastProvider } from "@/components/ui/toast-provider";
import "./globals.css";

export const metadata: Metadata = {
  applicationName: "Enterprise CRM",
  title: { default: "Enterprise CRM", template: "%s · Enterprise CRM" },
  description: "A bilingual B2B revenue workspace for customer relationships, pipeline and execution.",
  category: "business",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html
      lang="en"
      dir="ltr"
      className="h-full antialiased"
      suppressHydrationWarning
    >
      <head>
        <Script id="theme-bootstrap" strategy="beforeInteractive">
          {themeBootstrapScript}
        </Script>
        <Script id="locale-bootstrap" strategy="beforeInteractive">
          {localeBootstrapScript}
        </Script>
      </head>
      <body className="min-h-full flex flex-col">
        <I18nProvider>
          <ThemeProvider>
            <ToastProvider><AuthProvider>{children}</AuthProvider></ToastProvider>
          </ThemeProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
