"use client";

import { useUIStore, type Locale } from "./ui-store";

/**
 * Lightweight UI-chrome i18n (EN/HI). Broadcast content itself is already
 * multi-language via the pipeline; this covers navigation and shared labels.
 * A future pass can migrate to next-intl route-based localization.
 */
const dictionaries = {
  en: {
    "nav.dashboard": "Dashboard",
    "nav.news": "News",
    "nav.portal": "Portal",
    "nav.skip": "Skip to main content",
    "brand.tagline": "AI News Network",
    "status.live": "LIVE",
    "status.online": "Online",
    "status.offline": "Offline",
    "theme.toggle": "Switch theme",
    "locale.toggle": "Change language",
    "common.loading": "Loading…",
    "common.error": "Something went wrong",
    "common.retry": "Retry",
    "common.close": "Close",
    "common.save": "Save",
    "common.cancel": "Cancel",
  },
  hi: {
    "nav.dashboard": "डैशबोर्ड",
    "nav.news": "समाचार",
    "nav.portal": "पोर्टल",
    "nav.skip": "मुख्य सामग्री पर जाएँ",
    "brand.tagline": "एआई न्यूज़ नेटवर्क",
    "status.live": "लाइव",
    "status.online": "ऑनलाइन",
    "status.offline": "ऑफ़लाइन",
    "theme.toggle": "थीम बदलें",
    "locale.toggle": "भाषा बदलें",
    "common.loading": "लोड हो रहा है…",
    "common.error": "कुछ गड़बड़ हो गई",
    "common.retry": "पुनः प्रयास",
    "common.close": "बंद करें",
    "common.save": "सहेजें",
    "common.cancel": "रद्द करें",
  },
} satisfies Record<Locale, Record<string, string>>;

export type TranslationKey = keyof (typeof dictionaries)["en"];

export function useT() {
  const locale = useUIStore((s) => s.locale);
  return (key: TranslationKey): string => dictionaries[locale][key] ?? dictionaries.en[key] ?? key;
}
