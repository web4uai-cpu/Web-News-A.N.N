"use client";

import { useForm } from "react-hook-form";
import { AnimatePresence, motion } from "framer-motion";
import { api } from "@/lib/api";
import { useToastStore } from "@/components/ui/toast";
import { X } from "lucide-react";

const SETTING_GROUPS = [
  {
    title: "📰 News Sources",
    fields: [
      { key: "NEWS_API_KEY", label: "NewsAPI Key" },
      { key: "ALPHA_VANTAGE_KEY", label: "AlphaVantage Key" },
    ],
  },
  {
    title: "🧠 AI / LLM",
    fields: [{ key: "LLM_API_KEY", label: "Primary LLM API Key" }],
  },
  {
    title: "🎬 Media",
    fields: [
      { key: "ELEVENLABS_API_KEY", label: "ElevenLabs API Key" },
      { key: "HEYGEN_API_KEY", label: "HeyGen Video Key" },
    ],
  },
  {
    title: "📱 Social Media",
    fields: [
      { key: "TWITTER_BEARER_TOKEN", label: "Twitter/X Bearer Token" },
      { key: "FACEBOOK_PAGE_TOKEN", label: "Facebook Page Token" },
      { key: "INSTAGRAM_ACCESS_TOKEN", label: "Instagram Access Token" },
    ],
  },
];

interface Props {
  open: boolean;
  onClose: () => void;
}

export function SettingsModal({ open, onClose }: Props) {
  const { register, handleSubmit, reset } = useForm();
  const toast = useToastStore((s) => s.add);

  const onSubmit = handleSubmit(async (data) => {
    const payload: Record<string, string> = {};
    for (const [k, v] of Object.entries(data)) {
      if (typeof v === "string" && v.trim()) payload[k] = v.trim();
    }
    if (Object.keys(payload).length === 0) {
      toast("No changes to save", "info");
      return;
    }
    try {
      const result = await api.saveSettings(payload);
      toast(result.message || "Settings saved!", "success");
      reset();
      onClose();
    } catch (e: any) {
      toast(`Failed: ${e.message}`, "error");
    }
  });

  const inputClass =
    "w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-white/30 outline-none focus:border-indigo-500/50";

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-white/10 bg-[#151525] p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <button onClick={onClose} className="absolute right-4 top-4 text-muted hover:text-white">
              <X className="h-5 w-5" />
            </button>

            <h2 className="mb-6 text-lg font-bold">⚙️ System API Keys</h2>

            <form onSubmit={onSubmit} className="space-y-6">
              {SETTING_GROUPS.map((group) => (
                <div key={group.title}>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
                    {group.title}
                  </h3>
                  <div className="space-y-3">
                    {group.fields.map((field) => (
                      <div key={field.key}>
                        <label className="mb-1 block text-xs text-muted">{field.label}</label>
                        <input
                          {...register(field.key)}
                          type="password"
                          placeholder="Leave empty to keep current"
                          className={inputClass}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              <div className="flex justify-end">
                <button
                  type="submit"
                  className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500"
                >
                  Save Configurations
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
