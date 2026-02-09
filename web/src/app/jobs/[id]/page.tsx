"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import { getJob, getJobLogs, cancelJob, getDownloadUrl, getSubtitlesUrl, createJobWebSocket } from "@/lib/api";

type JobData = Record<string, unknown>;
type LogEntry = { timestamp: string; level: string; message: string };

export default function JobDetail() {
  const params = useParams();
  const jobId = String(params.id);
  const [job, setJob] = useState<JobData | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [showLogs, setShowLogs] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Fetch job data
  const fetchJob = useCallback(() => {
    getJob(jobId).then(setJob).catch(() => setError("Erro ao carregar job"));
  }, [jobId]);

  const fetchLogs = useCallback(() => {
    getJobLogs(jobId, 200).then(setLogs).catch(() => {});
  }, [jobId]);

  // Initial load + polling
  useEffect(() => {
    fetchJob();
    fetchLogs();
    const interval = setInterval(() => {
      fetchJob();
      fetchLogs();
    }, 3000);
    return () => clearInterval(interval);
  }, [fetchJob, fetchLogs]);

  // WebSocket for real-time updates
  useEffect(() => {
    try {
      const ws = createJobWebSocket(jobId);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "progress" || data.type === "status") {
            setJob((prev) => (prev ? { ...prev, ...data } : data));
          }
          if (data.type === "log") {
            setLogs((prev) => [...prev.slice(-500), data]);
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onerror = () => {};
      ws.onclose = () => {};

      return () => {
        ws.close();
      };
    } catch {
      // WebSocket not available, rely on polling
      return;
    }
  }, [jobId]);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleCancel = async () => {
    if (!confirm("Cancelar este job?")) return;
    setCancelling(true);
    try {
      await cancelJob(jobId);
      fetchJob();
    } catch {
      setError("Erro ao cancelar");
    }
    setCancelling(false);
  };

  if (!job && !error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-800 rounded w-1/3" />
          <div className="h-4 bg-gray-800 rounded w-1/2" />
          <div className="h-64 bg-gray-800 rounded" />
        </div>
      </div>
    );
  }

  const config = ((job?.config || {}) as Record<string, unknown>);
  const progress = ((job?.progress || {}) as Record<string, unknown>);
  const status = String(job?.status || "unknown");
  const isActive = status === "running" || status === "queued";
  const isCompleted = status === "completed";
  const isFailed = status === "failed";

  const stages = [
    "Download", "Transcricao", "Traducao", "Split",
    "TTS", "Fade In/Out", "Sincronizacao", "Concatenacao",
    "Pos-Processamento", "Mux Final"
  ];

  const currentStage = Number(progress.current_stage || 0);

  const statusConfig: Record<string, { color: string; label: string }> = {
    running: { color: "text-blue-400", label: "Em andamento" },
    completed: { color: "text-green-400", label: "Concluido" },
    failed: { color: "text-red-400", label: "Falhou" },
    queued: { color: "text-yellow-400", label: "Na fila" },
    cancelled: { color: "text-gray-400", label: "Cancelado" },
  };

  const sc = statusConfig[status] || { color: "text-gray-400", label: status };

  return (
    <div className="max-w-4xl mx-auto">
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6 text-red-400">{error}</div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold font-mono">{jobId}</h1>
            <span className={`text-lg font-medium ${sc.color}`}>{sc.label}</span>
          </div>
          <p className="text-gray-500 text-sm">
            {String(config.src_lang || "auto")} &rarr; {String(config.tgt_lang || "pt")}
            <span className="mx-2">|</span>TTS: {String(config.tts_engine || "edge")}
            <span className="mx-2">|</span>Traducao: {String(config.translation_engine || "m2m100")}
            <span className="mx-2">|</span>Tipo: {String(config.content_type || "palestra")}
          </p>
        </div>
        <div className="flex gap-2">
          {isActive && (
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="bg-red-600 hover:bg-red-700 disabled:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            >
              {cancelling ? "Cancelando..." : "Cancelar"}
            </button>
          )}
          <a href="/jobs" className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
            Voltar
          </a>
        </div>
      </div>

      {/* Progress */}
      {(isActive || isCompleted) && (
        <section className="border border-gray-800 rounded-lg p-5 mb-6">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-semibold">Progresso</h2>
            <span className="text-2xl font-bold font-mono text-blue-400">{String(progress.percent || (isCompleted ? 100 : 0))}%</span>
          </div>

          {/* Overall progress bar */}
          <div className="bg-gray-800 rounded-full h-3 mb-4">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${isCompleted ? "bg-green-500" : "bg-blue-500"}`}
              style={{ width: `${progress.percent || (isCompleted ? 100 : 0)}%` }}
            />
          </div>

          {/* Stage indicators */}
          <div className="grid grid-cols-5 gap-2 text-xs">
            {stages.map((stage, i) => {
              const stageNum = i + 1;
              const isDone = stageNum < currentStage || isCompleted;
              const isCurrent = stageNum === currentStage && isActive;
              return (
                <div
                  key={stage}
                  className={`p-2 rounded text-center border ${
                    isDone
                      ? "border-green-500/30 bg-green-500/10 text-green-400"
                      : isCurrent
                      ? "border-blue-500/30 bg-blue-500/10 text-blue-400 animate-pulse"
                      : "border-gray-800 text-gray-600"
                  }`}
                >
                  <div className="font-medium">{stageNum}</div>
                  <div className="mt-0.5">{stage}</div>
                </div>
              );
            })}
          </div>

          {isActive && !!progress.stage_name && (
            <div className="mt-3 text-sm text-gray-400">
              Etapa atual: <span className="text-white font-medium">{String(progress.stage_name)}</span>
              {!!progress.detail && <span className="ml-2 text-gray-500">- {String(progress.detail)}</span>}
            </div>
          )}
        </section>
      )}

      {/* Error display */}
      {isFailed && !!job?.error && (
        <section className="border border-red-500/30 bg-red-500/5 rounded-lg p-5 mb-6">
          <h2 className="text-lg font-semibold text-red-400 mb-2">Erro</h2>
          <pre className="text-sm text-red-300 whitespace-pre-wrap font-mono">{String(job.error)}</pre>
        </section>
      )}

      {/* Results */}
      {isCompleted && (
        <section className="border border-green-500/30 bg-green-500/5 rounded-lg p-5 mb-6">
          <h2 className="text-lg font-semibold text-green-400 mb-4">Resultado</h2>

          {/* Video player */}
          <div className="bg-black rounded-lg overflow-hidden mb-4">
            <video
              controls
              className="w-full"
              src={getDownloadUrl(jobId)}
            >
              Seu navegador nao suporta o elemento video.
            </video>
          </div>

          {/* Download buttons */}
          <div className="flex flex-wrap gap-3">
            <a
              href={getDownloadUrl(jobId)}
              download
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Download Video Dublado
            </a>
            <a
              href={getSubtitlesUrl(jobId, "orig")}
              download
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            >
              Legendas Original (SRT)
            </a>
            <a
              href={getSubtitlesUrl(jobId, "trad")}
              download
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            >
              Legendas Traduzidas (SRT)
            </a>
          </div>

          {/* Metrics */}
          {!!job?.duration_s && (
            <div className="mt-4 text-sm text-gray-400">
              Tempo total de processamento: <span className="text-white">{String(job.duration_s)}s</span>
            </div>
          )}
        </section>
      )}

      {/* Configuration */}
      <section className="border border-gray-800 rounded-lg p-5 mb-6">
        <h2 className="text-lg font-semibold mb-3">Configuracao</h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div><span className="text-gray-500">Input:</span> <span className="text-gray-300 break-all">{String(config.input || "-")}</span></div>
          <div><span className="text-gray-500">Idiomas:</span> {String(config.src_lang || "auto")} &rarr; {String(config.tgt_lang || "pt")}</div>
          <div><span className="text-gray-500">TTS:</span> {String(config.tts_engine || "edge")}</div>
          <div><span className="text-gray-500">Traducao:</span> {String(config.translation_engine || "m2m100")}</div>
          <div><span className="text-gray-500">Whisper:</span> {String(config.whisper_model || "large-v3")}</div>
          <div><span className="text-gray-500">Sync:</span> {String(config.sync_mode || "smart")}</div>
          <div><span className="text-gray-500">Tipo:</span> {String(config.content_type || "palestra")}</div>
          <div><span className="text-gray-500">Max Stretch:</span> {String(config.maxstretch || "1.3")}x</div>
          {!!config.voice && <div><span className="text-gray-500">Voz:</span> {String(config.voice)}</div>}
          {!!config.ollama_model && <div><span className="text-gray-500">Ollama:</span> {String(config.ollama_model)}</div>}
          {!!config.diarize && <div><span className="text-gray-500">Diarizacao:</span> Sim</div>}
          {!!config.clone_voice && <div><span className="text-gray-500">Clone Voz:</span> Sim</div>}
        </div>
      </section>

      {/* Logs */}
      <section className="border border-gray-800 rounded-lg p-5">
        <button
          type="button"
          onClick={() => setShowLogs(!showLogs)}
          className="flex items-center gap-2 text-lg font-semibold hover:text-blue-400 transition-colors"
        >
          <span className={`transform transition-transform text-sm ${showLogs ? "rotate-90" : ""}`}>&#9654;</span>
          Logs ({logs.length})
        </button>

        {showLogs && (
          <div className="mt-3 bg-gray-950 rounded-lg p-3 max-h-96 overflow-y-auto font-mono text-xs">
            {logs.length === 0 ? (
              <div className="text-gray-600">Nenhum log disponivel</div>
            ) : (
              logs.map((log, i) => {
                const levelColors: Record<string, string> = {
                  INFO: "text-blue-400",
                  WARNING: "text-yellow-400",
                  ERROR: "text-red-400",
                  DEBUG: "text-gray-600",
                };
                return (
                  <div key={i} className="py-0.5">
                    <span className="text-gray-600">{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ""}</span>{" "}
                    <span className={levelColors[log.level] || "text-gray-400"}>[{log.level || "INFO"}]</span>{" "}
                    <span className="text-gray-300">{log.message}</span>
                  </div>
                );
              })
            )}
            <div ref={logsEndRef} />
          </div>
        )}
      </section>
    </div>
  );
}
