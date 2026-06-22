"use client";

import { Key } from "lucide-react";

export function ApiTab() {
  return (
    <div className="rounded-[30px] border border-white/5 bg-glass p-8 backdrop-blur-xl">
      <div className="mb-6 flex items-center gap-3 text-xs font-semibold uppercase tracking-wider text-muted">
        <Key className="h-4 w-4" /> API Authentication
      </div>
      <p className="mb-4 text-sm text-muted">
        Use this secure token to programmatically fetch JSON news arrays or connect to our Real-Time Websocket Node.
      </p>

      <div className="rounded-2xl border border-white/10 bg-black p-4 font-mono text-sm text-muted">
        <span>X-ANN-API-Key: </span>
        <span className="cursor-pointer blur-sm transition-all hover:blur-none">
          ann_sk_ent_94f8b22a01qc74
        </span>
      </div>

      <h3 className="mt-8 text-lg font-black">cURL Example — JSON Feed</h3>
      <div className="mt-3 rounded-2xl border border-white/10 bg-black p-4 font-mono text-sm">
        <pre className="text-violet-300 whitespace-pre-wrap">{`curl -X GET "https://api.ann.network/feed/json?category=technology" \\
  -H "X-ANN-API-Key: ann_sk_ent_94f8..."`}</pre>
      </div>
    </div>
  );
}
