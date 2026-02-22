#!/usr/bin/env python3
"""Baixador de videos usando yt-dlp (YouTube, TikTok, Instagram, Facebook, etc.)."""

import argparse
import json
import sys
from pathlib import Path


def write_checkpoint(dub_work_dir: Path, step: int):
    cp = {"last_step_num": step}
    (dub_work_dir / "checkpoint.json").write_text(json.dumps(cp))


def main():
    parser = argparse.ArgumentParser(description="Baixar video com yt-dlp")
    parser.add_argument("--url", required=True, help="URL do video (YouTube, TikTok, etc.)")
    parser.add_argument("--outdir", required=True, help="Diretorio de saida")
    parser.add_argument(
        "--quality",
        default="best",
        choices=["best", "1080p", "720p", "480p", "audio"],
        help="Qualidade do download",
    )
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # dub_work para checkpoint (compativel com job_manager)
    dub_work = outdir.parent / "dub_work"
    dub_work.mkdir(parents=True, exist_ok=True)

    print(f"[baixar] URL: {args.url}", flush=True)
    print(f"[baixar] Qualidade: {args.quality}", flush=True)
    print(f"[baixar] Saida: {outdir}", flush=True)

    write_checkpoint(dub_work, 0)

    try:
        import yt_dlp
    except ImportError:
        print("[baixar] ERRO: yt-dlp nao instalado. Instale com: pip install yt-dlp", flush=True)
        sys.exit(1)

    outtmpl = str(outdir / "video.%(ext)s")

    if args.quality == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    elif args.quality == "1080p":
        ydl_opts = {
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
        }
    elif args.quality == "720p":
        ydl_opts = {
            "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
        }
    elif args.quality == "480p":
        ydl_opts = {
            "format": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best",
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
        }
    else:  # best
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
        }

    print("[baixar] Iniciando download...", flush=True)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([args.url])

    # Verificar se arquivo foi criado
    files = list(outdir.glob("video.*"))
    if not files:
        print("[baixar] ERRO: Nenhum arquivo baixado encontrado", flush=True)
        sys.exit(1)

    print(f"[baixar] Download concluido: {files[0].name} ({files[0].stat().st_size // 1024 // 1024}MB)", flush=True)
    write_checkpoint(dub_work, 1)


if __name__ == "__main__":
    main()
