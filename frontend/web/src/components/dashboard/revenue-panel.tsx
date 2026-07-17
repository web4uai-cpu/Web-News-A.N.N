"use client";

import { DollarSign, TrendingUp, Users, CreditCard, ArrowUpRight } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { TIER_COLORS } from "@/lib/chart-theme";
import { Card } from "@/components/ui";

export function RevenuePanel() {
  const { data } = useQuery({
    queryKey: ["dashboard-revenue"],
    queryFn: () => api.dashboardRevenue(),
    refetchInterval: 30000,
  });

  const totalClients = data?.total_clients ?? 0;
  const totalRequests = data?.total_api_requests ?? 0;
  const tierBreakdown = data?.tier_breakdown ?? {};
  const clients = data?.clients ?? [];

  const tierEntries = Object.entries(tierBreakdown);

  const kpis = [
    {
      label: "B2B Clients",
      value: totalClients.toString(),
      change: `${tierEntries.length} tiers`,
      Icon: Users,
      color: "text-violet-400",
    },
    {
      label: "API Requests",
      value: totalRequests.toLocaleString(),
      change: "total",
      Icon: CreditCard,
      color: "text-cyan-400",
    },
    {
      label: "Top Tier",
      value: tierEntries.length > 0 ? tierEntries.sort((a, b) => b[1] - a[1])[0][0] : "--",
      change: tierEntries.length > 0 ? `${tierEntries.sort((a, b) => b[1] - a[1])[0][1]} clients` : "",
      Icon: TrendingUp,
      color: "text-blue-400",
    },
    {
      label: "Revenue",
      value: `$${(totalClients * 99).toLocaleString()}`,
      change: "est. MRR",
      Icon: DollarSign,
      color: "text-emerald-400",
    },
  ];

  return (
    <Card className="rounded-xl p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <DollarSign className="h-4 w-4 text-emerald-400" />
          Revenue
        </h2>
        <span className="text-[10px] text-muted">Live data</span>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="rounded-lg bg-white/5 p-2.5">
            <div className="flex items-center gap-1 text-[10px] text-muted">
              <kpi.Icon className={`h-3 w-3 ${kpi.color}`} />
              {kpi.label}
            </div>
            <div className="mt-1 text-base font-bold">{kpi.value}</div>
            <div className="flex items-center gap-0.5 text-[9px] text-emerald-400">
              <ArrowUpRight className="h-2.5 w-2.5" />
              {kpi.change}
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
        <div>
          <div className="mb-2 text-[10px] font-semibold text-muted">Tier Breakdown</div>
          <div className="space-y-2">
            {tierEntries.map(([tier, count]) => (
              <div key={tier} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
                <div className="flex items-center gap-2">
                  <span aria-hidden className="h-2.5 w-2.5 rounded-full" style={{ background: TIER_COLORS[tier] || TIER_COLORS.pro }} />
                  <span className="text-xs font-medium capitalize">{tier}</span>
                </div>
                <span className="text-xs font-bold">{count} clients</span>
              </div>
            ))}
            {tierEntries.length === 0 && (
              <div className="text-xs text-muted text-center py-4">No tier data available</div>
            )}
          </div>
        </div>

        <div>
          <div className="mb-2 text-[10px] font-semibold text-muted">Active Clients</div>
          <div className="space-y-1.5 max-h-48 overflow-y-auto">
            {clients.map((c) => (
              <div key={c.name} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
                <div className="min-w-0">
                  <div className="truncate text-xs font-medium">{c.name}</div>
                  <div className="text-[9px] text-muted capitalize">{c.tier}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold">{c.requests_used.toLocaleString()}</div>
                  <div className="text-[9px] text-muted">/ {c.monthly_quota.toLocaleString()}</div>
                </div>
              </div>
            ))}
            {clients.length === 0 && (
              <div className="text-xs text-muted text-center py-4">No clients yet</div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
