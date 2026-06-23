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

  const langConfig = [
    { code: "en" as const, label: "🇬🇧 English", dir: "ltr" as const },
    { code: "hi" as const, label: "🇮🇳 हिन्दी", dir: "ltr" as const },
    { code: "es" as const, label: "🇪🇸 Español", dir: "ltr" as const },
    { code: "fr" as const, label: "🇫🇷 Français", dir: "ltr" as const },
    { code: "ar" as const, label: "🇸🇦 العربية", dir: "rtl" as const },
  ];

  const getScriptText = () => {
    if (!activeScript) return "";
    const map: Record<string, string> = {
      en: activeScript.english_script,
      hi: activeScript.hindi_script,
      es: activeScript.spanish_script ?? activeScript.english_script,
      fr: activeScript.french_script ?? activeScript.english_script,
      ar: activeScript.arabic_script ?? activeScript.english_script,
    };
    return map[readerLang] ?? activeScript.english_script;
  };

  const currentDir = langConfig.find((l) => l.code === readerLang)?.dir ?? "ltr";

  const copyScript = () => {
    if (!activeScript) return;
    navigator.clipboard.writeText(getScriptText());
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
              <div className="mb-4 flex flex-wrap gap-1">
                {langConfig.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => setReaderLang(lang.code)}
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                      readerLang === lang.code ? "bg-indigo-500/20 text-indigo-400" : "text-muted hover:text-white"
                    }`}
                  >
                    {lang.label}
                  </button>
                ))}
              </div>

              <div className="whitespace-pre-line text-sm leading-relaxed text-muted" dir={currentDir}>
                {getScriptText()?.replace(/\[PAUSE\]/g, "\n\n— PAUSE —\n\n")}
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
