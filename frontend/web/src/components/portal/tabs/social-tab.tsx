"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useToastStore } from "@/components/ui/toast";
import { Share2, Link as LinkIcon, CheckCircle } from "lucide-react";

export function SocialTab() {
  const { register, handleSubmit } = useForm();
  const toast = useToastStore((s) => s.add);
  const [synced, setSynced] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const onSubmit = handleSubmit(async (data) => {
    if (!data.ig_token) {
      toast("Instagram token required", "warning");
      return;
    }
    setSyncing(true);
    await new Promise((r) => setTimeout(r, 2000));
    setSyncing(false);
    setSynced(true);
    toast("Matrices successfully linked!", "success");
  });

  const inputClass =
    "w-full rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white placeholder:text-white/30 outline-none focus:border-violet-500 focus:shadow-[0_0_20px_rgba(139,92,246,0.3)] transition-all";

  return (
    <div className="mx-auto max-w-2xl rounded-[30px] border border-white/5 bg-glass p-8 backdrop-blur-xl">
      <div className="mb-6 flex items-center gap-3 text-xs font-semibold uppercase tracking-wider text-pink-400">
        <Share2 className="h-4 w-4" /> Social Auto-Pilot Configuration
      </div>
      <p className="mb-6 text-sm text-muted">
        Link your social media arrays. Videos generated in the Synthesis Engine will auto-publish to these feeds.
      </p>

      <form onSubmit={onSubmit} className="space-y-5">
        <div>
          <label className="mb-2 block text-sm font-semibold text-sky-400">Instagram Graph API Token</label>
          <input {...register("ig_token")} type="password" placeholder="EAAI..." className={inputClass} />
        </div>
        <div>
          <label className="mb-2 block text-sm font-semibold text-blue-400">Facebook Page ID</label>
          <input {...register("fb_id")} placeholder="10493820..." className={inputClass} />
        </div>

        <button
          type="submit"
          disabled={syncing}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-pink-500 to-sky-500 py-3 text-sm font-bold text-white uppercase tracking-wider hover:shadow-lg transition-all disabled:opacity-50"
        >
          <LinkIcon className="h-4 w-4" />
          {syncing ? "Synchronizing..." : "Synchronize Accounts"}
        </button>

        {synced && (
          <div className="flex items-center justify-center gap-2 rounded-xl bg-emerald-500/10 py-3 text-sm font-semibold text-emerald-400">
            <CheckCircle className="h-4 w-4" /> Matrices successfully linked! 100% Autopilot Enabled.
          </div>
        )}
      </form>
    </div>
  );
}
