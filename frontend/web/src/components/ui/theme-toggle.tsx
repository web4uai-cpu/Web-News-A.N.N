"use client";

import { Moon, Sun, Languages } from "lucide-react";
import { useUIStore } from "@/lib/ui-store";
import { useT } from "@/lib/i18n";

export function ThemeToggle() {
  const theme = useUIStore((s) => s.theme);
  const toggleTheme = useUIStore((s) => s.toggleTheme);
  const t = useT();
  return (
    <button
      onClick={toggleTheme}
      aria-label={t("theme.toggle")}
      title={t("theme.toggle")}
      className="rounded-lg p-2 text-muted transition-colors hover:bg-surface-hover hover:text-foreground"
    >
      {theme === "dark" ? <Sun className="h-4 w-4" aria-hidden /> : <Moon className="h-4 w-4" aria-hidden />}
    </button>
  );
}

export function LocaleToggle() {
  const locale = useUIStore((s) => s.locale);
  const setLocale = useUIStore((s) => s.setLocale);
  const t = useT();
  return (
    <button
      onClick={() => setLocale(locale === "en" ? "hi" : "en")}
      aria-label={t("locale.toggle")}
      title={t("locale.toggle")}
      className="flex items-center gap-1 rounded-lg p-2 text-xs font-semibold text-muted transition-colors hover:bg-surface-hover hover:text-foreground"
    >
      <Languages className="h-4 w-4" aria-hidden />
      {locale === "en" ? "हि" : "EN"}
    </button>
  );
}
