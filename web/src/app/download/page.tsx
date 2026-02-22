"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createDownloadJob } from "@/lib/api";

const QUALITY_OPTIONS = [
  { value: "best", label: "Melhor qualidade", desc: "Video + audio na melhor resolucao disponivel" },
  { value: "1080p", label: "1080p (Full HD)", desc: "Limitar a 1920x1080" },
  { value: "720p", label: "720p (HD)", desc: "Limitar a 1280x720" },
  { value: "480p", label: "480p (SD)", desc: "Limitar a 854x480" },
  { value: "audio", label: "So audio (MP3)", desc: "Extrair apenas o audio em MP3 192kbps" },
];

const SUPPORTED_SITES = [
  { name: "YouTube", color: "text-red-400" },
  { name: "TikTok", color: "text-pink-400" },
  { name: "Instagram", color: "text-purple-400" },
  { name: "Facebook", color: "text-blue-400" },
  { name: "Twitter/X", color: "text-sky-400" },
  { name: "Twitch", color: "text-violet-400" },
  { name: "+1000 sites", color: "text-gray-400" },
];

export default function DownloadPage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [quality, setQuality] = useState("best");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError(null);

    try {
      const job = await createDownloadJob({ url: url.trim(), quality }) as Record<string, unknown>;
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError(String(err));
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Baixar Video</h1>
        <p className="text-gray-400">Cole o link do video e baixe diretamente para o servidor</p>
      </div>

      {/* Sites suportados */}
      <div className="flex flex-wrap gap-2 mb-6">
        {SUPPORTED_SITES.map((site) => (
          <span key={site.name} className={`text-xs px-2 py-1 bg-gray-800 rounded-full border border-gray-700 ${site.color}`}>
            {site.name}
          </span>
        ))}
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6 text-red-400">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* URL */}
        <section className="border border-gray-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-3">Link do Video</h2>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:border-green-500 focus:outline-none"
            required
            autoFocus
          />
          <p className="text-xs text-gray-500 mt-2">
            Suporta qualquer plataforma compativel com yt-dlp
          </p>
        </section>

        {/* Qualidade */}
        <section className="border border-gray-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold mb-3">Qualidade</h2>
          <div className="space-y-2">
            {QUALITY_OPTIONS.map((opt) => (
              <label key={opt.value} className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                quality === opt.value
                  ? "border-green-500 bg-green-500/10"
                  : "border-gray-700 hover:border-gray-600"
              }`}>
                <input
                  type="radio"
                  name="quality"
                  value={opt.value}
                  checked={quality === opt.value}
                  onChange={() => setQuality(opt.value)}
                  className="mt-0.5"
                />
                <div>
                  <div className="font-medium text-sm">{opt.label}</div>
                  <div className="text-xs text-gray-500">{opt.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </section>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium text-lg transition-colors"
        >
          {loading ? "Iniciando download..." : "Baixar Video"}
        </button>
      </form>
    </div>
  );
}
