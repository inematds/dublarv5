import type { Metadata } from "next";
import "./globals.css";
import { NavVersion } from "./nav-version";

export const metadata: Metadata = {
  title: "Dublar Pro - Pipeline de Dublagem",
  description: "Interface web para dublagem automatica de videos com IA",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <nav className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <a href="/" className="text-xl font-bold text-white flex items-baseline gap-1">
              Dublar <span className="text-blue-400">Pro</span>
              <NavVersion />
            </a>
            <div className="flex gap-6 text-sm">
              <a href="/" className="hover:text-white transition-colors text-gray-400">Dashboard</a>
              <a href="/new" className="hover:text-blue-400 transition-colors text-blue-300">🎙 Dublar</a>
              <a href="/transcribe" className="hover:text-purple-400 transition-colors text-purple-300">📝 Transcrever</a>
              <a href="/cut" className="hover:text-orange-400 transition-colors text-orange-300">✂ Cortar</a>
              <a href="/download" className="hover:text-green-400 transition-colors text-green-300">⬇ Baixar</a>
              <a href="/jobs" className="hover:text-white transition-colors text-gray-400">Jobs</a>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
