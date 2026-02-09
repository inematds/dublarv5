"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getOptions, createJob } from "@/lib/api";

type Options = {
  tts_engines: { id: string; name: string; needs_gpu: boolean; needs_internet: boolean }[];
  translation_engines: { id: string; name: string; models: string[] | string }[];
  whisper_models: { id: string; name: string; quality: string }[];
  edge_voices: Record<string, { id: string; name: string; gender: string }[]>;
  bark_voices: Record<string, { id: string; name: string }[]>;
  content_types: { id: string; name: string; description: string; presets: Record<string, unknown> }[];
  languages: { code: string; name: string }[];
  ollama_models: { id: string; name: string; size_gb: number }[];
};

export default function NewJob() {
  const router = useRouter();
  const [options, setOptions] = useState<Options | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [input, setInput] = useState("");
  const [srcLang, setSrcLang] = useState("");
  const [tgtLang, setTgtLang] = useState("pt");
  const [contentType, setContentType] = useState("palestra");
  const [ttsEngine, setTtsEngine] = useState("edge");
  const [voice, setVoice] = useState("");
  const [asrEngine] = useState("whisper");
  const [whisperModel, setWhisperModel] = useState("large-v3");
  const [translationEngine, setTranslationEngine] = useState("m2m100");
  const [ollamaModel, setOllamaModel] = useState("qwen2.5:14b");
  const [largeModel, setLargeModel] = useState(false);
  const [diarize, setDiarize] = useState(false);
  const [cloneVoice, setCloneVoice] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [syncMode, setSyncMode] = useState("smart");
  const [maxstretch, setMaxstretch] = useState(1.3);
  const [seed, setSeed] = useState(42);

  useEffect(() => {
    getOptions().then(setOptions).catch(() => setError("API offline"));
  }, []);

  // Aplicar presets do tipo de conteudo
  useEffect(() => {
    if (!options) return;
    const ct = options.content_types.find((c) => c.id === contentType);
    if (ct) {
      if (ct.presets.sync) setSyncMode(String(ct.presets.sync));
      if (ct.presets.maxstretch) setMaxstretch(Number(ct.presets.maxstretch));
    }
  }, [contentType, options]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input) return;
    setLoading(true);
    setError(null);

    try {
      const config: Record<string, unknown> = {
        input,
        tgt_lang: tgtLang,
        tts_engine: ttsEngine,
        asr_engine: asrEngine,
        whisper_model: whisperModel,
        translation_engine: translationEngine,
        sync_mode: syncMode,
        maxstretch,
        seed,
        content_type: contentType,
      };
      if (srcLang) config.src_lang = srcLang;
      if (voice) config.voice = voice;
      if (translationEngine === "ollama") config.ollama_model = ollamaModel;
      if (largeModel) config.large_model = true;
      if (diarize) config.diarize = true;
      if (cloneVoice) config.clone_voice = true;

      const job = await createJob(config);
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError(String(err));
      setLoading(false);
    }
  };

  const langCode = tgtLang.startsWith("pt") ? "pt-BR" : tgtLang === "en" ? "en-US" : `${tgtLang}-${tgtLang.toUpperCase()}`;
  const edgeVoices = options?.edge_voices[langCode] || [];
  const barkVoices = options?.bark_voices[tgtLang] || [];

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">Nova Dublagem</h1>
      <p className="text-gray-400 mb-8">Configure o pipeline de dublagem do seu video</p>

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
            onChange={(e) => setInput(e.target.value)}
            placeholder="URL do YouTube ou caminho do arquivo local"
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
            required
          />
        </section>

        {/* Idiomas */}
        <section className="border border-gray-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Idiomas</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Origem (vazio = auto-detect)</label>
              <select value={srcLang} onChange={(e) => setSrcLang(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
                <option value="">Auto-detect</option>
                {options?.languages.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Destino</label>
              <select value={tgtLang} onChange={(e) => setTgtLang(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
                {options?.languages.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
              </select>
            </div>
          </div>
        </section>

        {/* Tipo de Conteudo */}
        <section className="border border-gray-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Tipo de Conteudo</h2>
          <div className="space-y-3">
            {options?.content_types.map((ct) => (
              <label key={ct.id}
                className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  contentType === ct.id ? "border-blue-500 bg-blue-500/10" : "border-gray-700 hover:border-gray-600"
                }`}>
                <input type="radio" name="contentType" value={ct.id}
                  checked={contentType === ct.id} onChange={(e) => setContentType(e.target.value)}
                  className="mt-1" />
                <div>
                  <div className="font-medium">{ct.name}</div>
                  <div className="text-sm text-gray-400">{ct.description}</div>
                </div>
              </label>
            ))}
          </div>
        </section>

        {/* Motores */}
        <section className="border border-gray-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-4">Motores de IA</h2>

          {/* TTS */}
          <div className="mb-4">
            <label className="block text-sm text-gray-400 mb-1">Motor TTS (Voz)</label>
            <select value={ttsEngine} onChange={(e) => { setTtsEngine(e.target.value); setVoice(""); }}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
              {options?.tts_engines.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name} {e.needs_gpu ? "(GPU)" : ""} {e.needs_internet ? "(Online)" : "(Offline)"}
                </option>
              ))}
            </select>
          </div>

          {/* Voz */}
          {ttsEngine === "edge" && edgeVoices.length > 0 && (
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">Voz Edge TTS</label>
              <select value={voice} onChange={(e) => setVoice(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
                <option value="">Padrao</option>
                {edgeVoices.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
              </select>
            </div>
          )}
          {ttsEngine === "bark" && barkVoices.length > 0 && (
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">Voz Bark</label>
              <select value={voice} onChange={(e) => setVoice(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
                <option value="">Padrao (Speaker 3)</option>
                {barkVoices.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
              </select>
            </div>
          )}

          {/* Clone Voice */}
          {ttsEngine === "xtts" && (
            <label className="flex items-center gap-2 mb-4 text-sm">
              <input type="checkbox" checked={cloneVoice} onChange={(e) => setCloneVoice(e.target.checked)} />
              Clonar voz do video original
            </label>
          )}

          {/* Traducao */}
          <div className="mb-4">
            <label className="block text-sm text-gray-400 mb-1">Motor de Traducao</label>
            <select value={translationEngine} onChange={(e) => setTranslationEngine(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
              {options?.translation_engines.map((e) => (
                <option key={e.id} value={e.id}>{e.name}</option>
              ))}
            </select>
          </div>

          {/* Modelo Ollama */}
          {translationEngine === "ollama" && (
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-1">Modelo Ollama</label>
              <select value={ollamaModel} onChange={(e) => setOllamaModel(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
                {options?.ollama_models.map((m) => (
                  <option key={m.id} value={m.id}>{m.name} ({m.size_gb}GB)</option>
                ))}
              </select>
            </div>
          )}

          {translationEngine === "m2m100" && (
            <label className="flex items-center gap-2 mb-4 text-sm">
              <input type="checkbox" checked={largeModel} onChange={(e) => setLargeModel(e.target.checked)} />
              Usar modelo grande (M2M100 1.2B - melhor qualidade)
            </label>
          )}

          {/* Whisper */}
          <div>
            <label className="block text-sm text-gray-400 mb-1">Modelo Whisper (ASR)</label>
            <select value={whisperModel} onChange={(e) => setWhisperModel(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
              {options?.whisper_models.map((m) => (
                <option key={m.id} value={m.id}>{m.name} - {m.quality}</option>
              ))}
            </select>
          </div>
        </section>

        {/* Opcoes Avancadas */}
        <section className="border border-gray-800 rounded-lg p-5">
          <button type="button" onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
            <span className={`transform transition-transform ${showAdvanced ? "rotate-90" : ""}`}>&#9654;</span>
            Opcoes Avancadas
          </button>

          {showAdvanced && (
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Modo de Sync</label>
                  <select value={syncMode} onChange={(e) => setSyncMode(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white">
                    <option value="smart">Smart (recomendado)</option>
                    <option value="fit">Fit (comprimir/esticar)</option>
                    <option value="pad">Pad (silencio)</option>
                    <option value="extend">Extend (freeze frame)</option>
                    <option value="none">None (sem sync)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Max Stretch: {maxstretch}x</label>
                  <input type="range" min="1" max="2" step="0.05" value={maxstretch}
                    onChange={(e) => setMaxstretch(Number(e.target.value))}
                    className="w-full" />
                </div>
              </div>

              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={diarize} onChange={(e) => setDiarize(e.target.checked)} />
                Detectar multiplos falantes (diarizacao)
              </label>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Seed</label>
                <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))}
                  className="w-32 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white" />
              </div>
            </div>
          )}
        </section>

        {/* Submit */}
        <button type="submit" disabled={loading || !input}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed
            text-white px-6 py-3 rounded-lg font-medium text-lg transition-colors">
          {loading ? "Iniciando..." : "Iniciar Dublagem"}
        </button>
      </form>
    </div>
  );
}
