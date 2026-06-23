"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useToastStore } from "@/components/ui/toast";
import { Share2, CheckCircle, XCircle, Loader2 } from "lucide-react";

const PLATFORMS = [
  { key: "twitter", label: "Twitter / X", color: "text-sky-400", envHint: "TWITTER_BEARER_TOKEN" },
  { key: "facebook", label: "Facebook Page", color: "text-blue-400", envHint: "FACEBOOK_PAGE_TOKEN + FACEBOOK_PAGE_ID" },
  { key: "instagram", label: "Instagram", color: "text-pink-400", envHint: "INSTAGRAM_ACCESS_TOKEN + INSTAGRAM_ACCOUNT_ID" },
];

export function SocialTab() {
  const toast = useToastStore((s) => s.add);
  const [testing, setTesting] = useState<string | null>(null);

  const { data: status, refetch } = useQuery({
    queryKey: ["social-status"],
    queryFn: () => api.socialStatus(),
    refetchInterval: 10000,
  });

  const testPlatform = async (platform: string) => {
    setTesting(platform);
    try {
      const result = await api.socialTestConnection(platform);
      toast(`${platform}: ${result.message}`, result.status === "ok" ? "success" : "warning");
      refetch();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Connection test failed";
      toast(`${platform}: ${msg}`, "error");
    } finally {
      setTesting(null);
    }
  };

  const enabledPlatforms = status?.enabled_platforms ?? [];
  const autoPost = status?.auto_post ?? false;

  return (
    <div className="mx-auto max-w-2xl rounded-[30px] border border-white/5 bg-glass p-8 backdrop-blur-xl">
      <div className="mb-6 flex items-center gap-3 text-xs font-semibold uppercase tracking-wider text-pink-400">
        <Share2 className="h-4 w-4" /> Social Auto-Pilot Configuration
      </div>

      <div className="mb-6 flex items-center gap-2 rounded-xl bg-white/5 px-4 py-3">
        <span className={`h-2.5 w-2.5 rounded-full ${autoPost ? "bg-emerald-500 live-dot" : "bg-amber-500"}`} />
        <span className="text-sm font-medium">
          Auto-Post: <span className={autoPost ? "text-emerald-400" : "text-amber-400"}>{autoPost ? "ENABLED" : "DISABLED"}</span>
        </span>
        <span className="ml-auto text-[10px] text-muted">
          Set SOCIAL_AUTO_POST=true in .env to enable
        </span>
      </div>

      <p className="mb-6 text-sm text-muted">
        Configure social media credentials in your backend <code className="rounded bg-white/10 px-1.5 py-0.5 text-xs">.env</code> file.
        Each platform below shows its connection status in real-time.
      </p>

      <div className="space-y-3">
        {PLATFORMS.map((p) => {
          const isEnabled = enabledPlatforms.includes(p.key);
          const isTesting = testing === p.key;
          return (
            <div key={p.key} className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/40 px-5 py-4">
              <div className="flex items-center gap-3">
                <span className={`h-3 w-3 rounded-full ${isEnabled ? "bg-emerald-500" : "bg-red-500/60"}`} />
                <div>
                  <div className={`text-sm font-semibold ${p.color}`}>{p.label}</div>
                  <div className="text-[10px] text-muted">{p.envHint}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xs font-medium ${isEnabled ? "text-emerald-400" : "text-red-400"}`}>
                  {isEnabled ? "Connected" : "Not configured"}
                </span>
                {isEnabled ? (
                  <CheckCircle className="h-4 w-4 text-emerald-400" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-400/60" />
                )}
                <button
                  onClick={() => testPlatform(p.key)}
                  disabled={isTesting}
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-muted hover:bg-white/10 transition-colors disabled:opacity-50"
                >
                  {isTesting ? <Loader2 className="h-3 w-3 animate-spin" /> : "Test"}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {enabledPlatforms.length > 0 && (
        <div className="mt-6 flex items-center justify-center gap-2 rounded-xl bg-emerald-500/10 py-3 text-sm font-semibold text-emerald-400">
          <CheckCircle className="h-4 w-4" />
          {enabledPlatforms.length} platform{enabledPlatforms.length > 1 ? "s" : ""} connected
          {autoPost ? " — Auto-pilot active" : ""}
        </div>
      )}
    </div>
  );
}
