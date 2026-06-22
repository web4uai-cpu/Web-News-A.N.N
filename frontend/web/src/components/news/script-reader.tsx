"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useNewsStore } from "@/lib/store";
import { useToastStore } from "@/components/ui/toast";
import { timeAgo } from "@/lib/utils";
import { X, Copy } from "lucide-react";
import { useEffect } from "react";

export function ScriptReader() {
  const { activeScript, setActiveScript, readerLang, setReaderLang } = useNewsStore();
  const toast = useToastStore((s) => s.add);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setActiveScript(null);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const copyScript = () => {
    if (!activeScript) return;
    const text = readerLang === "hi" ? activeScript.hindi_script : activeScript.english_script;
    navigator.clipboard.writeText(text);
    toast("Script copied!", "success");
  };

  return (
    <AnimatePresence>
      {activeScript && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={() => setActiveScript(null)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="relative max-h-[85vh] w-full max-w-2xl overflow-hidden rounded-2xl border border-white/10 bg-[#0f0f1e]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="border-b border-white/5 p-5">
              <div className="flex items-start justify-between">
                <div>
                  <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase text-indigo-400">
                    {activeScript.category}
                  </span>
                  <h2 className="mt-2 text-lg font-bold leading-tight">{activeScript.headline}</h2>
                  <div className="mt-2 flex gap-3 text-[10px] text-muted">
                    <span>{timeAgo(activeScript.created_at)}</span>
                    <span>•</span>
                    <span>
                      {readerLang === "hi" ? activeScript.word_count_hi : activeScript.word_count_en} words
                    </span>
                    <span>•</span>
                    <span>~{activeScript.estimated_duration_seconds}s</span>
                  </div>
                </div>
                <button
                  onClick={() => setActiveScript(null)}
                  className="rounded-lg p-1 text-muted hover:bg-white/10 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Body */}
            <div className="max-h-[55vh] overflow-y-auto p-5">
              <div className="mb-4 flex gap-1">
                <button
                  onClick={() => setReaderLang("en")}
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    readerLang === "en" ? "bg-indigo-500/20 text-indigo-400" : "text-muted hover:text-white"
                  }`}
                >
                  🇬🇧 English
                </button>
                <button
                  onClick={() => setReaderLang("hi")}
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    readerLang === "hi" ? "bg-indigo-500/20 text-indigo-400" : "text-muted hover:text-white"
                  }`}
                >
                  🇮🇳 हिन्दी
                </button>
              </div>

              <div className="whitespace-pre-line text-sm leading-relaxed text-muted">
                {(readerLang === "hi" ? activeScript.hindi_script : activeScript.english_script)
                  ?.replace(/\[PAUSE\]/g, "\n\n— PAUSE —\n\n")}
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between border-t border-white/5 p-4">
              <div className="text-[10px] text-muted">⏱️ Broadcast ready</div>
              <button
                onClick={copyScript}
                className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-muted hover:bg-white/10 hover:text-white"
              >
                <Copy className="h-3.5 w-3.5" /> Copy Script
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
