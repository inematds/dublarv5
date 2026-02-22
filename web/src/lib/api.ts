// API calls use relative URLs → routed through Next.js rewrites proxy
// This works whether accessing via localhost or remote IP
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

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

export async function getOllamaStatus() {
  return fetchApi("/api/ollama/status");
}

export async function startOllama() {
  return fetchApi("/api/ollama/start", { method: "POST" });
}

export async function stopOllama() {
  return fetchApi("/api/ollama/stop", { method: "POST" });
}

export async function pullOllamaModel(model: string) {
  return fetchApi("/api/ollama/pull", { method: "POST", body: JSON.stringify({ model }) });
}

export async function createJob(config: Record<string, unknown>) {
  return fetchApi("/api/jobs", { method: "POST", body: JSON.stringify(config) });
}

export async function createJobWithUpload(
  file: File,
  config: Record<string, unknown>,
  onProgress?: (percent: number) => void,
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("config_json", JSON.stringify(config));

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/api/jobs/upload`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || `HTTP ${xhr.status}`));
        } catch {
          reject(new Error(`HTTP ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => reject(new Error("Erro de rede no upload"));
    xhr.ontimeout = () => reject(new Error("Upload timeout"));
    xhr.timeout = 600000; // 10 min

    xhr.send(formData);
  });
}

export async function createCutJob(config: Record<string, unknown>) {
  return fetchApi("/api/jobs/cut", { method: "POST", body: JSON.stringify(config) });
}

export async function createCutJobWithUpload(
  file: File,
  config: Record<string, unknown>,
  onProgress?: (percent: number) => void,
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("config_json", JSON.stringify(config));

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/api/jobs/cut/upload`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || `HTTP ${xhr.status}`));
        } catch {
          reject(new Error(`HTTP ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => reject(new Error("Erro de rede no upload"));
    xhr.ontimeout = () => reject(new Error("Upload timeout"));
    xhr.timeout = 600000;

    xhr.send(formData);
  });
}

export async function createDownloadJob(config: Record<string, unknown>) {
  return fetchApi("/api/jobs/download", { method: "POST", body: JSON.stringify(config) });
}

export async function createTranscriptionJob(config: Record<string, unknown>) {
  return fetchApi("/api/jobs/transcribe", { method: "POST", body: JSON.stringify(config) });
}

export async function createTranscriptionJobWithUpload(
  file: File,
  config: Record<string, unknown>,
  onProgress?: (percent: number) => void,
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("config_json", JSON.stringify(config));

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/api/jobs/transcribe/upload`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        try {
          const err = JSON.parse(xhr.responseText);
          reject(new Error(err.detail || `HTTP ${xhr.status}`));
        } catch {
          reject(new Error(`HTTP ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => reject(new Error("Erro de rede no upload"));
    xhr.ontimeout = () => reject(new Error("Upload timeout"));
    xhr.timeout = 600000;

    xhr.send(formData);
  });
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

export async function retryJob(jobId: string) {
  return fetchApi(`/api/jobs/${jobId}/retry`, { method: "POST" });
}

export async function deleteJob(jobId: string) {
  return fetchApi(`/api/jobs/${jobId}?delete=true`, { method: "DELETE" });
}

export function getDownloadUrl(jobId: string) {
  return `${API_BASE}/api/jobs/${jobId}/download`;
}

export function getSubtitlesUrl(jobId: string, lang = "trad") {
  return `${API_BASE}/api/jobs/${jobId}/subtitles?lang=${lang}`;
}

export async function getClips(jobId: string) {
  return fetchApi(`/api/jobs/${jobId}/clips`);
}

export function getClipUrl(jobId: string, clipName: string) {
  return `${API_BASE}/api/jobs/${jobId}/clips/${clipName}`;
}

export function getClipsZipUrl(jobId: string) {
  return `${API_BASE}/api/jobs/${jobId}/clips/zip`;
}

export function getTranscriptUrl(jobId: string, format: "srt" | "txt" | "json" = "srt") {
  return `${API_BASE}/api/jobs/${jobId}/transcript?format=${format}`;
}

export async function getTranscriptSummary(jobId: string) {
  return fetchApi(`/api/jobs/${jobId}/transcript-summary`);
}

export async function getVideoSummary(jobId: string) {
  return fetchApi(`/api/jobs/${jobId}/video-summary`);
}

export function getDownloadFileUrl(jobId: string) {
  return `${API_BASE}/api/jobs/${jobId}/download-file`;
}

export function createJobWebSocket(jobId: string): WebSocket {
  const wsProtocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsHost = typeof window !== "undefined" ? window.location.host : "localhost:8000";
  // WebSocket goes directly to backend on port 8000 (Next.js doesn't proxy WS)
  const backendHost = wsHost.replace(":3000", ":8000");
  return new WebSocket(`${wsProtocol}//${backendHost}/ws/jobs/${jobId}`);
}
