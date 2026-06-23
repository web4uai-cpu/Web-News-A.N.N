"use client";

export default function AdminDashboard() {
  const stats = [
    { label: "Active Services", value: "7/7", color: "text-green-400" },
    { label: "Articles Today", value: "142", color: "text-indigo-400" },
    { label: "Pipeline Success", value: "98.2%", color: "text-cyan-400" },
    { label: "Monthly Revenue", value: "$12,400", color: "text-amber-400" },
    { label: "Active Users", value: "1,847", color: "text-violet-400" },
    { label: "B2B Clients", value: "23", color: "text-rose-400" },
  ];

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">System Overview</h1>

      <div className="mb-8 grid grid-cols-3 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-xl border border-white/10 bg-[#0f0f1e] p-5">
            <p className="text-xs text-gray-500">{stat.label}</p>
            <p className={`mt-1 text-2xl font-bold ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-xl border border-white/10 bg-[#0f0f1e] p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-400">Service Health</h2>
          <div className="space-y-2">
            {[
              "API Gateway", "Auth Service", "Article Service",
              "Video Service", "Notification Service", "Analytics", "Search",
            ].map((svc) => (
              <div key={svc} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-sm">
                <span>{svc}</span>
                <span className="rounded-full bg-green-500/20 px-2 py-0.5 text-xs text-green-400">
                  Operational
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-[#0f0f1e] p-5">
          <h2 className="mb-4 text-sm font-semibold text-gray-400">Recent Pipeline Runs</h2>
          <div className="space-y-2">
            {[
              { id: "pipe-001", time: "2 min ago", status: "completed", articles: 5 },
              { id: "pipe-002", time: "15 min ago", status: "completed", articles: 8 },
              { id: "pipe-003", time: "32 min ago", status: "completed", articles: 3 },
              { id: "pipe-004", time: "1 hr ago", status: "failed", articles: 0 },
              { id: "pipe-005", time: "1.5 hr ago", status: "completed", articles: 6 },
            ].map((run) => (
              <div key={run.id} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-sm">
                <span className="font-mono text-xs text-gray-500">{run.id}</span>
                <span className="text-xs text-gray-500">{run.time}</span>
                <span className="text-xs">{run.articles} articles</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    run.status === "completed"
                      ? "bg-green-500/20 text-green-400"
                      : "bg-red-500/20 text-red-400"
                  }`}
                >
                  {run.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
