const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getSystemStatus() {
  return fetchApi("/api/system/status");
}

export async function getOptions() {
  return fetchApi("/api/models/options");
}

export async function getOllamaModels() {
  return fetchApi("/api/models/ollama");
}

export async function createJob(config: Record<string, unknown>) {
  return fetchApi("/api/jobs", { method: "POST", body: JSON.stringify(config) });
}

export async function listJobs() {
  return fetchApi("/api/jobs");
}

export async function getJob(jobId: string) {
  return fetchApi(`/api/jobs/${jobId}`);
}

export async function getJobLogs(jobId: string, lastN = 100) {
  return fetchApi(`/api/jobs/${jobId}/logs?last_n=${lastN}`);
}

export async function cancelJob(jobId: string) {
  return fetchApi(`/api/jobs/${jobId}`, { method: "DELETE" });
}

export function getDownloadUrl(jobId: string) {
  return `${API_BASE}/api/jobs/${jobId}/download`;
}

export function getSubtitlesUrl(jobId: string, lang = "trad") {
  return `${API_BASE}/api/jobs/${jobId}/subtitles?lang=${lang}`;
}

export function createJobWebSocket(jobId: string): WebSocket {
  const wsBase = API_BASE.replace("http", "ws");
  return new WebSocket(`${wsBase}/ws/jobs/${jobId}`);
}
