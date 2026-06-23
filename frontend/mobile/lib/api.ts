const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
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

export interface Script {
  id: string;
  headline: string;
  english_script: string;
  hindi_script: string;
  category: string;
  word_count_en: number;
  word_count_hi: number;
  estimated_duration_seconds: number;
  created_at: string;
}

export const api = {
  scripts: (limit = 50) => apiFetch<Script[]>(`/api/v1/scripts?limit=${limit}`),
  health: () => apiFetch<{ status: string }>("/health"),
};
