"use client";

import { useState } from "react";

interface FlaggedArticle {
  id: string;
  headline: string;
  category: string;
  flag_type: "copyright" | "defamation" | "pii" | "bias";
  severity: "low" | "medium" | "high";
  flagged_at: string;
  flagged_by: string;
  excerpt: string;
  status: "pending" | "approved" | "rejected" | "edited";
}

const MOCK_QUEUE: FlaggedArticle[] = [
  {
    id: "art-101",
    headline: "Tech Giant Faces Antitrust Probe",
    category: "technology",
    flag_type: "defamation",
    severity: "high",
    flagged_at: "2026-06-23T10:15:00Z",
    flagged_by: "Legal Agent",
    excerpt: "The CEO has been accused of deliberately misleading investors about...",
    status: "pending",
  },
  {
    id: "art-102",
    headline: "Healthcare Data Breach Exposes Millions",
    category: "health",
    flag_type: "pii",
    severity: "high",
    flagged_at: "2026-06-23T09:30:00Z",
    flagged_by: "Legal Agent",
    excerpt: "Patient records including names, SSNs, and medical histories of John Doe...",
    status: "pending",
  },
  {
    id: "art-103",
    headline: "Market Analysis: Q2 Earnings Preview",
    category: "finance",
    flag_type: "copyright",
    severity: "medium",
    flagged_at: "2026-06-23T08:00:00Z",
    flagged_by: "Legal Agent",
    excerpt: "According to the Reuters report published yesterday...",
    status: "pending",
  },
];

const SEVERITY_COLORS = {
  low: "bg-blue-500/20 text-blue-400",
  medium: "bg-amber-500/20 text-amber-400",
  high: "bg-red-500/20 text-red-400",
};

const FLAG_LABELS = {
  copyright: "Copyright",
  defamation: "Defamation Risk",
  pii: "PII Detected",
  bias: "Bias Concern",
};

export default function ModerationPage() {
  const [queue, setQueue] = useState(MOCK_QUEUE);
  const [selected, setSelected] = useState<FlaggedArticle | null>(null);

  const handleAction = (id: string, action: "approved" | "rejected") => {
    setQueue((q) => q.map((a) => (a.id === id ? { ...a, status: action } : a)));
    setSelected(null);
  };

  const pendingCount = queue.filter((a) => a.status === "pending").length;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Content Moderation</h1>
          <p className="text-sm text-gray-500">{pendingCount} items pending review</p>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-6">
        <div className="col-span-3 space-y-3">
          {queue.map((article) => (
            <div
              key={article.id}
              onClick={() => setSelected(article)}
              className={`cursor-pointer rounded-xl border p-4 transition-colors ${
                selected?.id === article.id
                  ? "border-indigo-500 bg-indigo-500/5"
                  : "border-white/10 bg-[#0f0f1e] hover:border-white/20"
              } ${article.status !== "pending" ? "opacity-50" : ""}`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium">{article.headline}</h3>
                  <p className="mt-1 text-xs text-gray-500">
                    {article.flagged_by} &middot; {new Date(article.flagged_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-xs ${SEVERITY_COLORS[article.severity]}`}>
                    {article.severity}
                  </span>
                  <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-gray-400">
                    {FLAG_LABELS[article.flag_type]}
                  </span>
                </div>
              </div>
              {article.status !== "pending" && (
                <span className={`mt-2 inline-block rounded-full px-2 py-0.5 text-xs ${
                  article.status === "approved" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                }`}>
                  {article.status}
                </span>
              )}
            </div>
          ))}
        </div>

        <div className="col-span-2">
          {selected ? (
            <div className="sticky top-8 rounded-xl border border-white/10 bg-[#0f0f1e] p-5">
              <h2 className="text-lg font-bold">{selected.headline}</h2>
              <div className="mt-3 space-y-3">
                <div>
                  <p className="text-xs font-semibold text-gray-500">Flag Type</p>
                  <p className="text-sm">{FLAG_LABELS[selected.flag_type]}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-500">Flagged Excerpt</p>
                  <p className="mt-1 rounded bg-red-500/5 p-3 text-sm text-red-300 border border-red-500/20">
                    {selected.excerpt}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-500">Category</p>
                  <p className="text-sm capitalize">{selected.category}</p>
                </div>
              </div>
              {selected.status === "pending" && (
                <div className="mt-6 flex gap-3">
                  <button
                    onClick={() => handleAction(selected.id, "approved")}
                    className="flex-1 rounded-lg bg-green-600 py-2 text-sm font-medium hover:bg-green-500"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleAction(selected.id, "rejected")}
                    className="flex-1 rounded-lg bg-red-600 py-2 text-sm font-medium hover:bg-red-500"
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex h-64 items-center justify-center rounded-xl border border-white/10 bg-[#0f0f1e] text-sm text-gray-500">
              Select an article to review
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
