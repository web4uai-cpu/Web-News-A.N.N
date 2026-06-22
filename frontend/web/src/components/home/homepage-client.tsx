"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useNewsStore } from "@/lib/store";
import { HomeNav } from "./home-nav";
import { HeroBroadcast } from "./hero-broadcast";
import { BreakingStrip } from "./breaking-strip";
import { TrendingStories } from "./trending-stories";
import { LiveMarkets } from "./live-markets";
import { AiBroadcastFeed } from "./ai-broadcast-feed";
import { HomeFooter } from "./home-footer";
import { ToastContainer } from "@/components/ui/toast";

export function HomepageClient() {
  const { setScripts } = useNewsStore();

  const { data: scripts } = useQuery({
    queryKey: ["home-scripts"],
    queryFn: () => api.scripts(50),
    refetchInterval: 30000,
  });

  useEffect(() => {
    if (scripts) setScripts(scripts);
  }, [scripts]);

  return (
    <div className="flex min-h-screen flex-col bg-[#05050a]">
      <HomeNav />
      <BreakingStrip />
      <HeroBroadcast />
      <TrendingStories />
      <LiveMarkets />
      <AiBroadcastFeed />
      <HomeFooter />
      <ToastContainer />
    </div>
  );
}
