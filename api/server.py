"""Dublar Pro API - FastAPI server com WebSocket para progresso em tempo real."""

import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.job_manager import JobManager
from api.model_manager import get_ollama_models, get_ollama_status, unload_ollama_model, start_ollama, stop_ollama, pull_ollama_model, get_all_options
from api.system_monitor import get_system_status
from api.stats_tracker import get_stats_summary

JOBS_DIR = Path(os.environ.get("JOBS_DIR", "jobs"))
UPLOAD_DIR = JOBS_DIR / "uploads"

job_manager = JobManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown."""
    JOBS_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    job_manager.start()
    yield


app = FastAPI(
    title="Dublar v5 API",
    version="5.2.0",
    description="API para pipeline de dublagem, corte e transcricao automatica de videos",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- System ---

@app.get("/api/system/status")
async def system_status():
    """Status completo do sistema (GPU, CPU, RAM, disco)."""
    status = get_system_status()
    status["ollama"] = await get_ollama_status()
    return status


# --- Models ---

@app.get("/api/models/options")
async def get_options():
    """Todas as opcoes disponiveis (TTS, ASR, traducao, idiomas, etc)."""
    options = get_all_options()
    options["ollama_models"] = await get_ollama_models()
    return options


@app.get("/api/models/ollama")
async def list_ollama_models():
    """Lista modelos Ollama disponiveis."""
    return await get_ollama_models()


@app.post("/api/models/ollama/unload")
async def unload_model(model: str):
    """Descarrega modelo Ollama para liberar VRAM."""
    success = await unload_ollama_model(model)
    return {"success": success, "model": model}


@app.post("/api/ollama/start")
async def api_start_ollama():
    """Inicia o servico Ollama."""
    return await start_ollama()


@app.post("/api/ollama/stop")
async def api_stop_ollama():
    """Para o servico Ollama."""
    return await stop_ollama()


@app.get("/api/ollama/status")
async def api_ollama_status():
    """Status do Ollama (online, modelos)."""
    status = await get_ollama_status()
    if status["online"]:
        status["models"] = await get_ollama_models()
    return status


@app.post("/api/ollama/pull")
async def api_pull_model(body: dict):
    """Baixa um modelo no Ollama."""
    model = body.get("model", "")
    if not model:
        raise HTTPException(400, "Campo 'model' obrigatorio")
    result = await pull_ollama_model(model)
    return result


# --- Jobs: Specific routes BEFORE {job_id} to avoid conflicts ---

@app.post("/api/jobs/cut")
async def create_cut_job(config: dict):
    """Criar job de corte de clips."""
    if "input" not in config:
        raise HTTPException(400, "Campo obrigatorio: input")
    config["job_type"] = "cutting"
    if "mode" not in config:
        config["mode"] = "manual"
    if config["mode"] == "manual" and not config.get("timestamps"):
        raise HTTPException(400, "Modo manual requer campo 'timestamps'")
    job = await job_manager.create_job(config)
    return job.to_dict()


@app.post("/api/jobs/cut/upload")
async def create_cut_job_with_upload(
    file: UploadFile = File(...),
    config_json: str = Form(...),
):
    """Criar job de corte com upload de video."""
    config = json.loads(config_json)
    suffix = Path(file.filename).suffix or ".mp4"
    safe_name = f"{uuid.uuid4().hex[:8]}_{Path(file.filename).stem}{suffix}"
    upload_path = UPLOAD_DIR / safe_name
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    config["input"] = str(upload_path.absolute())
    config["job_type"] = "cutting"
    if "mode" not in config:
        config["mode"] = "manual"
    job = await job_manager.create_job(config)
    return job.to_dict()


@app.post("/api/jobs/transcribe")
async def create_transcription_job(config: dict):
    """Criar job de transcricao."""
    if "input" not in config:
        raise HTTPException(400, "Campo obrigatorio: input")
    config["job_type"] = "transcription"
    job = await job_manager.create_job(config)
    return job.to_dict()


@app.post("/api/jobs/transcribe/upload")
async def create_transcription_job_with_upload(
    file: UploadFile = File(...),
    config_json: str = Form(...),
):
    """Criar job de transcricao com upload de video."""
    config = json.loads(config_json)
    suffix = Path(file.filename).suffix or ".mp4"
    safe_name = f"{uuid.uuid4().hex[:8]}_{Path(file.filename).stem}{suffix}"
    upload_path = UPLOAD_DIR / safe_name
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    config["input"] = str(upload_path.absolute())
    config["job_type"] = "transcription"
    job = await job_manager.create_job(config)
    return job.to_dict()


# --- Jobs: General endpoints ---

@app.post("/api/jobs")
async def create_job(config: dict):
    """Criar novo job de dublagem."""
    if "input" not in config or "tgt_lang" not in config:
        raise HTTPException(400, "Campos obrigatorios: input, tgt_lang")
    job = await job_manager.create_job(config)
    return job.to_dict()


@app.post("/api/jobs/upload")
async def create_job_with_upload(
    file: UploadFile = File(...),
    config_json: str = Form(...),
):
    """Criar job de dublagem com upload de video."""
    config = json.loads(config_json)

    # Salvar arquivo com nome unico para evitar conflitos
    suffix = Path(file.filename).suffix or ".mp4"
    safe_name = f"{uuid.uuid4().hex[:8]}_{Path(file.filename).stem}{suffix}"
    upload_path = UPLOAD_DIR / safe_name
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)

    config["input"] = str(upload_path.absolute())
    job = await job_manager.create_job(config)
    return job.to_dict()


@app.get("/api/jobs")
async def list_jobs():
    """Listar todos os jobs."""
    return job_manager.list_jobs()


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Status de um job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado")
    return job.to_dict()


@app.get("/api/jobs/{job_id}/logs")
async def get_job_logs(job_id: str, last_n: int = 100):
    """Ultimas linhas de log de um job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado")
    return {"logs": job.read_logs(last_n)}


@app.get("/api/jobs/{job_id}/download")
async def download_job(job_id: str):
    """Baixar video dublado."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado")
    if job.status != "completed":
        raise HTTPException(400, "Job nao concluido")

    # Procurar video de saida
    dublado_dir = job.workdir / "dublado"
    if dublado_dir.exists():
        videos = list(dublado_dir.glob("*.mp4"))
        if videos:
            return FileResponse(
                videos[0],
                media_type="video/mp4",
                filename=videos[0].name,
            )

    raise HTTPException(404, "Video dublado nao encontrado")


@app.get("/api/jobs/{job_id}/subtitles")
async def download_subtitles(job_id: str, lang: str = "trad"):
    """Baixar legendas (original ou traduzida)."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado")

    srt_name = "asr_trad.srt" if lang == "trad" else "asr.srt"
    srt_path = job.workdir / "dub_work" / srt_name
    if srt_path.exists():
        return FileResponse(srt_path, media_type="text/plain", filename=srt_name)
    raise HTTPException(404, "Legendas nao encontradas")


@app.get("/api/jobs/{job_id}/clips")
async def list_clips(job_id: str):
    """Lista os clips disponíveis para um job de corte."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado")
    if job.config.get("job_type") != "cutting":
        raise HTTPException(400, "Job nao e do tipo corte")

    clips_dir = job.workdir / "clips"
    if not clips_dir.exists():
        return []

    clips = []
    for clip in sorted(clips_dir.glob("clip_*.mp4")):
        clips.append({
            "name": clip.name,
            "size_bytes": clip.stat().st_size,
            "url": f"/api/jobs/{job_id}/clips/{clip.name}",
        })
    return clips


@app.get("/api/jobs/{job_id}/clips/zip")
async def download_clips_zip(job_id: str):
    """Download do ZIP com todos os clips."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado")

    zip_path = job.workdir / "clips" / "clips.zip"
    if not zip_path.exists():
        raise HTTPException(404, "ZIP nao encontrado")

    return FileResponse(zip_path, media_type="application/zip", filename=f"clips_{job_id}.zip")


@app.get("/api/jobs/{job_id}/clips/{clip_name}")
async def download_clip(job_id: str, clip_name: str):
    """Download de um clip individual."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado")

    # Validar nome do clip para evitar path traversal
    if ".." in clip_name or "/" in clip_name:
        raise HTTPException(400, "Nome de clip invalido")

    clip_path = job.workdir / "clips" / clip_name
    if not clip_path.exists():
        raise HTTPException(404, "Clip nao encontrado")

    return FileResponse(clip_path, media_type="video/mp4", filename=clip_name)


@app.get("/api/jobs/{job_id}/transcript")
async def download_transcript(job_id: str, format: str = "srt"):
    """Download da transcricao em diferentes formatos (srt, txt, json)."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado")
    if job.config.get("job_type") != "transcription":
        raise HTTPException(400, "Job nao e do tipo transcricao")

    valid_formats = {"srt": "text/plain", "txt": "text/plain", "json": "application/json"}
    if format not in valid_formats:
        raise HTTPException(400, f"Formato invalido. Use: {', '.join(valid_formats.keys())}")

    transcript_path = job.workdir / "transcription" / f"transcript.{format}"
    if not transcript_path.exists():
        raise HTTPException(404, f"Transcricao em formato {format} nao encontrada")

    return FileResponse(
        transcript_path,
        media_type=valid_formats[format],
        filename=f"transcript_{job_id}.{format}",
    )


@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancelar ou remover job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job nao encontrado")

    if job.status == "running":
        await job_manager.cancel_job(job_id)
        return {"status": "cancelled"}
    return {"status": job.status}


# --- WebSocket ---

@app.websocket("/ws/jobs/{job_id}")
async def websocket_job_progress(websocket: WebSocket, job_id: str):
    """WebSocket para progresso em tempo real de um job."""
    await websocket.accept()

    job = job_manager.get_job(job_id)
    if not job:
        await websocket.send_json({"error": "Job nao encontrado"})
        await websocket.close()
        return

    # Enviar estado atual
    await websocket.send_json({"event": "connected", "job": job.to_dict()})

    # Inscrever para updates
    job_manager.subscribe(job_id, websocket)

    try:
        while True:
            # Manter conexao aberta, receber pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        job_manager.unsubscribe(job_id, websocket)


# --- Health ---

@app.get("/api/stats")
async def pipeline_stats():
    """Estatisticas do pipeline (tempos medios, ETAs aprendidos)."""
    return get_stats_summary()


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "5.2.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
