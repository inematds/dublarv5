"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getOllamaStatus, startOllama, stopOllama, getOptions, createCutJob, createCutJobWithUpload } from "@/lib/api";

type OllamaModel = { id: string; name: string; size_gb: number };

export default function CutPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Input
  const [input, setInput] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // Mode
  const [mode, setMode] = useState<"manual" | "viral">("manual");

  // Manual
  const [timestamps, setTimestamps] = useState("");

  // Viral — clips
  const [numClips, setNumClips] = useState(5);
  const [minDuration, setMinDuration] = useState(30);
  const [maxDuration, setMaxDuration] = useState(120);
  const [whisperModel, setWhisperModel] = useState("large-v3");

  // LLM provider
  const [llmProvider, setLlmProvider] = useState<"ollama" | "openai" | "anthropic" | "groq" | "deepseek" | "together" | "openrouter" | "custom">("ollama");
  const [ollamaModel, setOllamaModel] = useState("qwen2.5:7b");
  const [llmModel, setLlmModel] = useState("");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [llmBaseUrl, setLlmBaseUrl] = useState("");

  // Ollama state
  const [ollamaOnline, setOllamaOnline] = useState<boolean | null>(null);
  const [ollamaModels, setOllamaModels] = useState<OllamaModel[]>([]);
  const [ollamaLoading, setOllamaLoading] = useState(false);
  const [ollamaSort, setOllamaSort] = useState<"size" | "name">("size");

  // Whisper models
  const [whisperModels, setWhisperModels] = useState<{ id: string; name: string; quality: string }[]>([]);

  useEffect(() => {
    getOptions().then((opts) => {
      if (opts.whisper_models) setWhisperModels(opts.whisper_models);
    }).catch(() => {});
  }, []);

  const refreshOllamaStatus = async () => {
    try {
      const st = await getOllamaStatus();
      setOllamaOnline(st.online);
      if (st.online && st.models) setOllamaModels(st.models);
    } catch {
      setOllamaOnline(false);
    }
  };

  useEffect(() => {
    if (mode === "viral") {
      refreshOllamaStatus();
      const interval = setInterval(refreshOllamaStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [mode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input && !uploadFile) return;
    setLoading(true);
    setError(null);
    setUploadProgress(null);

    try {
      const config: Record<string, unknown> = {
        input: uploadFile ? uploadFile.name : input,
        mode,
      };

      if (mode === "manual") {
        if (!timestamps.trim()) throw new Error("Informe os timestamps no modo manual");
        config.timestamps = timestamps.trim();
      } else {
        config.num_clips = numClips;
        config.min_duration = minDuration;
        config.max_duration = maxDuration;
        config.whisper_model = whisperModel;
        config.llm_provider = llmProvider;
        if (llmProvider === "ollama") {
          config.ollama_model = ollamaModel;
        } else {
          config.llm_model = llmModel;
          config.llm_api_key = llmApiKey;
          if (llmProvider === "custom") config.llm_base_url = llmBaseUrl;
        }
      }

      const job = uploadFile
        ? await createCutJobWithUpload(uploadFile, config, (p) => setUploadProgress(p))
        : await createCutJob(config);

      router.push(`/jobs/${(job as Record<string, unknown>).id}`);
    } catch (err) {
      setError(String(err));
      setLoading(false);
      setUploadProgress(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Cortar Video</h1>
        <p className="text-gray-400">Extraia clips por timestamps manuais ou deixe a IA identificar os momentos mais virais</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6 text-red-400">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Input */}
        <section className="border border-gray-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Video de Entrada</h2>
          <input
            type="text"
            value={input}
            onChange={(e) => { setInput(e.target.value); setUploadFile(null); }}
            placeholder="URL do YouTube"
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
            disabled={!!uploadFile}
            required={!uploadFile}
          />
          <div className="mt-3 flex items-center gap-3">
            <span className="text-sm text-gray-500">ou</span>
            <label className="cursor-pointer bg-gray-800 hover:bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-sm text-gray-300 transition-colors">
              {uploadFile ? uploadFile.name : "Enviar arquivo de video"}
              <input
                type="file"
                accept="video/*,audio/*"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) { setUploadFile(f); setInput(""); }
                }}
              />
            </label>
            {uploadFile && (
              <button type="button" onClick={() => setUploadFile(null)}
                className="text-sm text-red-400 hover:text-red-300">Remover</button>
            )}
          </div>
        </section>

        {/* Mode */}
        <section className="border border-gray-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Modo de Corte</h2>
          <div className="grid grid-cols-2 gap-3">
            <label className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-colors ${
              mode === "manual" ? "border-blue-500 bg-blue-500/10" : "border-gray-700 hover:border-gray-600"
            }`}>
              <input type="radio" checked={mode === "manual"} onChange={() => setMode("manual")} className="mt-1" />
              <div>
                <div className="font-medium">Manual</div>
                <div className="text-sm text-gray-400">Defina timestamps especificos</div>
              </div>
            </label>
            <label className={`flex items-start gap-3 p-4 rounded-lg border cursor-pointer transition-colors ${
              mode === "viral" ? "border-orange-500 bg-orange-500/10" : "border-gray-700 hover:border-gray-600"
            }`}>
              <input type="radio" checked={mode === "viral"} onChange={() => setMode("viral")} className="mt-1" />
              <div>
                <div className="font-medium">Viral (IA)</div>
                <div className="text-sm text-gray-400">LLM identifica os melhores momentos</div>
              </div>
            </label>
          </div>
        </section>

        {/* Manual config */}
        {mode === "manual" && (
          <section className="border border-gray-800 rounded-lg p-5">
            <h2 className="text-lg font-semibold mb-2">Timestamps</h2>
            <p className="text-sm text-gray-400 mb-3">
              Formatos aceitos: <code className="bg-gray-800 px-1 rounded">MM:SS-MM:SS</code> ou{" "}
              <code className="bg-gray-800 px-1 rounded">HH:MM:SS-HH:MM:SS</code>.
              Separe multiplos clips com virgula.
            </p>
            <textarea
              value={timestamps}
              onChange={(e) => setTimestamps(e.target.value)}
              placeholder={"00:30-02:15, 05:00-07:30\n10:45-12:00"}
              rows={3}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none font-mono text-sm"
              required
            />
            <p className="text-xs text-gray-500 mt-2">
              Exemplo: <code>00:30-02:15, 05:00-07:30</code> gera 2 clips (1m45s e 2m30s)
            </p>
          </section>
        )}

        {/* Viral config */}
        {mode === "viral" && (
          <section className="border border-orange-900/30 bg-orange-950/10 rounded-lg p-5 space-y-5">
            <h2 className="text-lg font-semibold">Configuracao Viral</h2>

            {/* Clips config */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Numero de clips</label>
                <input
                  type="number" min={1} max={20} value={numClips}
                  onChange={(e) => setNumClips(Number(e.target.value))}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Min. duracao (s)</label>
                <input
                  type="number" min={5} max={600} value={minDuration}
                  onChange={(e) => setMinDuration(Number(e.target.value))}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Max. duracao (s)</label>
                <input
                  type="number" min={5} max={600} value={maxDuration}
                  onChange={(e) => setMaxDuration(Number(e.target.value))}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white"
                />
              </div>
            </div>

            {/* Whisper model */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">Modelo Whisper (transcricao)</label>
              <select value={whisperModel} onChange={(e) => setWhisperModel(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
                {whisperModels.length > 0
                  ? whisperModels.map((m) => (
                    <option key={m.id} value={m.id}>{m.name} - {m.quality}</option>
                  ))
                  : <>
                    <option value="large-v3">large-v3 - Alta qualidade</option>
                    <option value="medium">medium - Balanceado</option>
                    <option value="small">small - Rapido</option>
                  </>
                }
              </select>
            </div>

            {/* LLM Provider selector */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Modelo de Analise (LLM)</label>
              <div className="flex gap-2 mb-3">
                {(["ollama", "openai", "anthropic", "groq", "deepseek", "together", "openrouter", "custom"] as const).map((p) => (
                  <button key={p} type="button" onClick={() => setLlmProvider(p)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                      llmProvider === p
                        ? "bg-orange-500/20 border-orange-500/50 text-orange-300"
                        : "bg-gray-900 border-gray-700 text-gray-400 hover:border-gray-500"
                    }`}>
                    {p === "ollama" ? "Ollama (local)" : p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>

              {/* Ollama local */}
              {llmProvider === "ollama" && (
                <div className="border border-gray-700 rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-2.5 h-2.5 rounded-full ${ollamaOnline ? "bg-green-500" : "bg-red-500"}`} />
                      <span className="text-sm font-medium">Ollama {ollamaOnline ? "Online" : "Offline"}</span>
                    </div>
                    <button type="button" disabled={ollamaLoading}
                      onClick={async () => {
                        setOllamaLoading(true);
                        try {
                          if (ollamaOnline) await stopOllama(); else await startOllama();
                          await refreshOllamaStatus();
                        } catch { /* ignore */ }
                        setOllamaLoading(false);
                      }}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors disabled:opacity-50 ${
                        ollamaOnline
                          ? "bg-red-600/20 text-red-400 border-red-500/30 hover:bg-red-600/30"
                          : "bg-green-600/20 text-green-400 border-green-500/30 hover:bg-green-600/30"
                      }`}>
                      {ollamaLoading ? "..." : ollamaOnline ? "Desligar" : "Ligar"}
                    </button>
                  </div>
                  {!ollamaOnline && (
                    <p className="text-sm text-yellow-400 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                      Ollama offline. Clique em "Ligar" ou escolha um provider externo acima.
                    </p>
                  )}
                  {ollamaOnline && ollamaModels.length > 0 && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-sm text-gray-400">Modelo</label>
                        <div className="flex gap-1">
                          {(["size", "name"] as const).map((s) => (
                            <button key={s} type="button" onClick={() => setOllamaSort(s)}
                              className={`px-2 py-0.5 rounded text-xs ${ollamaSort === s ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"}`}>
                              {s === "size" ? "Tamanho" : "A-Z"}
                            </button>
                          ))}
                        </div>
                      </div>
                      <div className="space-y-1.5 max-h-48 overflow-y-auto">
                        {[...ollamaModels]
                          .sort((a, b) => ollamaSort === "size" ? b.size_gb - a.size_gb : a.name.localeCompare(b.name))
                          .map((m) => {
                            const sel = ollamaModel === m.id;
                            const sizeColor = m.size_gb >= 30 ? "text-purple-400" : m.size_gb >= 10 ? "text-blue-400" : m.size_gb >= 5 ? "text-green-400" : "text-gray-400";
                            return (
                              <button type="button" key={m.id} onClick={() => setOllamaModel(m.id)}
                                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                                  sel ? "bg-orange-500/15 border border-orange-500/40 text-white" : "bg-gray-900 border border-gray-700/50 text-gray-300 hover:border-gray-600"
                                }`}>
                                <div className={`w-3 h-3 rounded-full border-2 flex-shrink-0 ${sel ? "border-orange-400 bg-orange-400" : "border-gray-600"}`} />
                                <span className="flex-1 font-medium">{m.name.split(":")[0]}</span>
                                {m.name.split(":")[1] && <span className="text-gray-500 text-xs">:{m.name.split(":")[1]}</span>}
                                <span className={`font-mono text-xs ${sizeColor}`}>{m.size_gb}GB</span>
                              </button>
                            );
                          })}
                      </div>
                    </div>
                  )}
                  {ollamaOnline && ollamaModels.length === 0 && (
                    <p className="text-sm text-yellow-400">Nenhum modelo instalado no Ollama.</p>
                  )}
                </div>
              )}

              {/* API Externa */}
              {llmProvider !== "ollama" && (
                <div className="border border-gray-700 rounded-lg p-4 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Modelo</label>
                      <input
                        type="text"
                        value={llmModel}
                        onChange={(e) => setLlmModel(e.target.value)}
                        placeholder={
                          llmProvider === "openai" ? "gpt-4o" :
                          llmProvider === "anthropic" ? "claude-sonnet-4-6" :
                          llmProvider === "groq" ? "llama-3.3-70b-versatile" :
                          llmProvider === "deepseek" ? "deepseek-chat" :
                          llmProvider === "together" ? "meta-llama/Llama-3-70b-chat-hf" :
                          llmProvider === "openrouter" ? "openai/gpt-4o" :
                          "model-name"
                        }
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">API Key</label>
                      <input
                        type="password"
                        value={llmApiKey}
                        onChange={(e) => setLlmApiKey(e.target.value)}
                        placeholder="sk-..."
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none"
                        required
                      />
                    </div>
                  </div>
                  {llmProvider === "custom" && (
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Base URL (compativel com OpenAI)</label>
                      <input
                        type="text"
                        value={llmBaseUrl}
                        onChange={(e) => setLlmBaseUrl(e.target.value)}
                        placeholder="https://meu-servidor.com"
                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:border-orange-500 focus:outline-none"
                        required
                      />
                    </div>
                  )}
                  <p className="text-xs text-gray-500">
                    {llmProvider === "openai" && "OpenAI — modelos GPT-4o, GPT-4o-mini, o1, etc."}
                    {llmProvider === "anthropic" && "Anthropic — Claude Sonnet, Haiku, Opus"}
                    {llmProvider === "groq" && "Groq — inferencia ultra-rapida (Llama, Mixtral, Gemma)"}
                    {llmProvider === "deepseek" && "DeepSeek — DeepSeek-V3, DeepSeek-R1"}
                    {llmProvider === "together" && "Together AI — modelos open-source hospedados"}
                    {llmProvider === "openrouter" && "OpenRouter — acesso unificado a 300+ modelos (GPT, Claude, Llama, Gemini...)"}
                    {llmProvider === "custom" && "Qualquer API compativel com OpenAI Chat Completions"}
                  </p>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Submit */}
        <div className="space-y-2">
          <button type="submit"
            disabled={loading || (!input && !uploadFile) || (mode === "viral" && llmProvider === "ollama" && !ollamaOnline) || (mode === "viral" && llmProvider !== "ollama" && (!llmModel || !llmApiKey))}
            className={`w-full disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium text-lg transition-colors ${
              mode === "viral"
                ? "bg-orange-600 hover:bg-orange-700"
                : "bg-blue-600 hover:bg-blue-700"
            }`}>
            {loading
              ? uploadProgress !== null
                ? `Enviando... ${uploadProgress}%`
                : "Iniciando..."
              : mode === "viral"
              ? "Analisar e Cortar"
              : "Cortar Video"}
          </button>
          {loading && uploadProgress !== null && (
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          )}
        </div>
      </form>
    </div>
  );
}
