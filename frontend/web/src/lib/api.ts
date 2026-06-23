const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function apiFetchSafe<T>(
  endpoint: string,
  fallback: T,
  options?: RequestInit
): Promise<T> {
  try {
    return await apiFetch<T>(endpoint, options);
  } catch {
    return fallback;
  }
}

export interface Script {
  id: string;
  headline: string;
  english_script: string;
  hindi_script: string;
  spanish_script?: string;
  french_script?: string;
  arabic_script?: string;
  category: string;
  word_count_en: number;
  word_count_hi: number;
  estimated_duration_seconds: number;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  uptime_seconds: number;
  active_jobs: number;
}

export interface PipelineJob {
  job_id: string;
  status: string;
  progress_pct: number;
  scripts?: Script[];
  errors?: string[];
}

export const api = {
  health: () => apiFetch<HealthResponse>("/health"),
  scripts: (limit = 50) => apiFetch<Script[]>(`/api/v1/scripts?limit=${limit}`),

  runPipeline: (params: {
    category: string;
    query?: string;
    max_articles: number;
    source: string;
    generate_media: boolean;
  }) =>
    apiFetch<{ job_id: string }>(
      `/api/v1/pipeline/run?generate_media=${params.generate_media}&source=${params.source}`,
      {
        method: "POST",
        body: JSON.stringify({
          category: params.category,
          query: params.query || null,
          max_articles: params.max_articles,
        }),
      }
    ),

  pipelineStatus: (jobId: string) =>
    apiFetch<PipelineJob>(`/api/v1/pipeline/status/${jobId}`),

  processArticle: (data: {
    source_url: string;
    raw_text: string;
    source_name: string;
    category: string;
  }) => apiFetch<Script>("/api/v1/process_news", { method: "POST", body: JSON.stringify(data) }),

  generateAudio: (scriptId: string, language = "en") =>
    apiFetch<{ status: string; audio_url?: string }>("/api/v1/media/generate_audio", {
      method: "POST",
      body: JSON.stringify({ script_id: scriptId, language }),
    }),

  getSettings: () => apiFetch<Record<string, string>>("/api/v1/admin/settings"),
  saveSettings: (payload: Record<string, string>) =>
    apiFetch<{ message: string }>("/api/v1/admin/settings", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  b2bCheckout: (tier = "pro", clientName = "ExternalFirm") =>
    apiFetch<{ checkout_url: string }>(
      `/api/v1/b2b/checkout?tier=${tier}&client_name=${clientName}`,
      { method: "POST" }
    ),

  // Dashboard real metrics
  dashboardAgents: () => apiFetch<AgentMetric[]>("/api/v1/dashboard/agents"),
  dashboardThroughput: () => apiFetch<ThroughputData>("/api/v1/dashboard/throughput"),
  dashboardRevenue: () => apiFetch<RevenueData>("/api/v1/dashboard/revenue"),
  dashboardMediaJobs: (limit = 20) => apiFetch<MediaJob[]>(`/api/v1/dashboard/media-jobs?limit=${limit}`),
  dashboardSystem: () => apiFetch<SystemMetrics>("/api/v1/dashboard/system"),

  // Social
  socialStatus: () => apiFetch<SocialStatus>("/api/v1/social/status"),
  socialBroadcast: (scriptId: string) =>
    apiFetch<Record<string, unknown>>(`/api/v1/social/broadcast/${scriptId}`, { method: "POST" }),
  socialTestConnection: (platform: string) =>
    apiFetch<{ status: string; message: string }>(`/api/v1/social/test/${platform}`, { method: "POST" }),
};

export interface AgentMetric {
  name: string;
  shortName?: string;
  tasks_completed: number;
  avg_latency: string;
  status: string;
  last_run: string;
}

export interface ThroughputData {
  total_today: number;
  avg_per_hour: number;
  hourly: { hour: string; articles: number }[];
  categories: { category: string; count: number }[];
}

export interface RevenueData {
  total_clients: number;
  total_api_requests: number;
  tier_breakdown: Record<string, number>;
  clients: { name: string; tier: string; requests_used: number; monthly_quota: number }[];
}

export interface MediaJob {
  id: string;
  script_id: string;
  headline: string;
  media_type: string;
  language: string;
  status: string;
  progress: number;
  duration: string;
  output_url: string;
  created_at: string;
}

export interface SystemMetrics {
  cpu_percent: number;
  memory_used_mb: number;
  memory_percent: number;
  disk_usage_percent: number;
  redis_status: string;
  celery_status: string;
  scripts_in_memory: number;
  social_platforms: string[];
  social_auto_post: boolean;
}

export interface SocialStatus {
  enabled_platforms: string[];
  auto_post: boolean;
}
