export function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

export function timeAgo(dateStr: string): string {
  if (!dateStr) return "";
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 60) return "Just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export const CATEGORIES = [
  { key: "all", label: "All News", icon: "📰" },
  { key: "technology", label: "Tech", icon: "💻" },
  { key: "business", label: "Business", icon: "💼" },
  { key: "politics", label: "Politics", icon: "🏛️" },
  { key: "finance", label: "Finance", icon: "📈" },
  { key: "health", label: "Health", icon: "🏥" },
  { key: "science", label: "Science", icon: "🔬" },
  { key: "sports", label: "Sports", icon: "⚽" },
  { key: "entertainment", label: "Entertainment", icon: "🎬" },
  { key: "geopolitics", label: "World", icon: "🌍" },
] as const;

export const CAT_COLORS: Record<string, string> = {
  technology: "#3b82f6",
  business: "#10b981",
  politics: "#f59e0b",
  finance: "#22d3ee",
  health: "#ec4899",
  science: "#a78bfa",
  sports: "#f97316",
  entertainment: "#e879f9",
  geopolitics: "#ef4444",
  general: "#6b7280",
};

export const PIPELINE_STEPS = [
  { key: "queued", label: "📋 Queue" },
  { key: "ingesting", label: "📡 Ingest" },
  { key: "extracting_facts", label: "🔍 Extract" },
  { key: "writing_script", label: "✍️ Script" },
  { key: "translating", label: "🌐 Translate" },
  { key: "generating_audio", label: "🎙️ Audio" },
  { key: "generating_video", label: "🎬 Video" },
  { key: "completed", label: "✅ Done" },
] as const;
