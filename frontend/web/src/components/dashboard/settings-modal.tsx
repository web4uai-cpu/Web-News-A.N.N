"use client";

import { useForm } from "react-hook-form";
import { api } from "@/lib/api";
import { useToastStore } from "@/components/ui/toast";
import { Button, Input, Modal } from "@/components/ui";

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
  const { register, handleSubmit, reset, formState } = useForm();
  const toast = useToastStore((s) => s.add);

  const onSubmit = handleSubmit(async (data) => {
    const adminToken = typeof data.ADMIN_TOKEN === "string" ? data.ADMIN_TOKEN.trim() : "";
    if (!adminToken) {
      toast("Admin token is required to change system keys", "error");
      return;
    }
    const payload: Record<string, string> = {};
    for (const [k, v] of Object.entries(data)) {
      if (k !== "ADMIN_TOKEN" && typeof v === "string" && v.trim()) payload[k] = v.trim();
    }
    if (Object.keys(payload).length === 0) {
      toast("No changes to save", "info");
      return;
    }
    try {
      const result = await api.saveSettings(payload, adminToken);
      toast(result.message || "Settings saved!", "success");
      reset();
      onClose();
    } catch (e) {
      toast(`Failed: ${e instanceof Error ? e.message : String(e)}`, "error");
    }
  });

  return (
    <Modal open={open} onClose={onClose} title="⚙️ System API Keys">
      <form onSubmit={onSubmit} className="space-y-6">
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-rose-400">
            🔐 Authorization
          </h3>
          <Input
            {...register("ADMIN_TOKEN")}
            type="password"
            label="Admin Token (required)"
            placeholder="X-Admin-Token value"
            autoComplete="off"
          />
        </div>

        {SETTING_GROUPS.map((group) => (
          <div key={group.title}>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-indigo-400">
              {group.title}
            </h3>
            <div className="space-y-3">
              {group.fields.map((field) => (
                <Input
                  key={field.key}
                  {...register(field.key)}
                  type="password"
                  label={field.label}
                  placeholder="Leave empty to keep current"
                  autoComplete="off"
                />
              ))}
            </div>
          </div>
        ))}

        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={formState.isSubmitting}>
            Save Configurations
          </Button>
        </div>
      </form>
    </Modal>
  );
}
