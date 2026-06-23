"use client";

import { useEffect, useRef } from "react";

type AdSize = "leaderboard" | "sidebar" | "in-feed" | "mobile-anchor";

const AD_DIMENSIONS: Record<AdSize, { width: number; height: number }> = {
  leaderboard: { width: 728, height: 90 },
  sidebar: { width: 300, height: 250 },
  "in-feed": { width: 336, height: 280 },
  "mobile-anchor": { width: 320, height: 50 },
};

interface AdPlacementProps {
  size: AdSize;
  adSlot: string;
  isPremium?: boolean;
  className?: string;
}

export function AdPlacement({ size, adSlot, isPremium, className = "" }: AdPlacementProps) {
  const adRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isPremium || !adRef.current) return;

    try {
      const w = window as any;
      (w.adsbygoogle = w.adsbygoogle || []).push({});
    } catch {
      // AdSense not loaded
    }
  }, [isPremium]);

  if (isPremium) return null;

  const dims = AD_DIMENSIONS[size];

  return (
    <div
      ref={adRef}
      className={`flex items-center justify-center overflow-hidden rounded-lg border border-white/5 bg-white/[0.02] ${className}`}
      style={{ minWidth: dims.width, minHeight: dims.height }}
    >
      <ins
        className="adsbygoogle"
        style={{ display: "inline-block", width: dims.width, height: dims.height }}
        data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
        data-ad-slot={adSlot}
      />
    </div>
  );
}

interface SponsoredCardProps {
  title: string;
  description: string;
  imageUrl: string;
  linkUrl: string;
  sponsor: string;
}

export function SponsoredCard({ title, description, imageUrl, linkUrl, sponsor }: SponsoredCardProps) {
  return (
    <a
      href={linkUrl}
      target="_blank"
      rel="noopener noreferrer sponsored"
      className="block rounded-xl border border-white/10 bg-[#0f0f1e] p-4 transition hover:border-white/20"
    >
      <div className="mb-2 flex items-center justify-between">
        <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-400">
          Sponsored
        </span>
        <span className="text-[10px] text-gray-600">{sponsor}</span>
      </div>
      <div className="aspect-video overflow-hidden rounded-lg bg-white/5">
        <img src={imageUrl} alt={title} className="h-full w-full object-cover" />
      </div>
      <h3 className="mt-3 text-sm font-semibold">{title}</h3>
      <p className="mt-1 text-xs text-gray-500 line-clamp-2">{description}</p>
    </a>
  );
}
