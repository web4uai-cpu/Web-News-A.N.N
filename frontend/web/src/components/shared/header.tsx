"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Radio } from "lucide-react";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";
import { LocaleToggle, ThemeToggle } from "@/components/ui";

const NAV_ITEMS = [
  { href: "/dashboard", key: "nav.dashboard" },
  { href: "/news", key: "nav.news" },
  { href: "/portal", key: "nav.portal" },
] as const;

export function Header() {
  const t = useT();
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-edge bg-panel backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2" aria-label="A.N.N. home">
          <Radio className="h-5 w-5 text-cyan-400" aria-hidden />
          <div>
            <div className="text-sm font-bold leading-none">A.N.N.</div>
            <div className="text-[10px] text-muted">{t("brand.tagline")}</div>
          </div>
        </Link>

        <nav aria-label="Primary" className="flex items-center gap-4 text-sm">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={pathname === item.href ? "page" : undefined}
              className={cn(
                "transition-colors",
                pathname === item.href
                  ? "font-semibold text-foreground"
                  : "text-muted hover:text-foreground"
              )}
            >
              {t(item.key)}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-1">
          <LocaleToggle />
          <ThemeToggle />
          <div className="ml-2 flex items-center gap-1.5 text-xs" role="status" aria-label={t("status.live")}>
            <span className="live-dot h-2 w-2 rounded-full bg-red-500" aria-hidden />
            <span className="font-semibold text-red-400">{t("status.live")}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
