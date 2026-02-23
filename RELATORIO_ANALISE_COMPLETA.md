# Relatorio de Analise Completa - inemaVOX (Dublar Pro v4)
## Data: 2026-02-09

---

# PARTE 1: ANALISE DA MAQUINA

## 1.1 Hardware

| Componente | Detalhes |
|------------|----------|
| **GPU** | NVIDIA GB10 (Blackwell Architecture) |
| **VRAM** | 40+ GB (confirmado pelo uso do Ollama) |
| **CUDA** | 13.0 (Driver 580.95.05) |
| **Compute Capability** | 12.1 |
| **CPU** | ARM64 (aarch64) - 20 cores |
| **Cores** | Cortex-X925 (high-perf) + Cortex-A725 (efficiency) |
| **RAM** | 119 GB |
| **Disco** | 3.7 TB NVMe (2.7 TB livre) |
| **Classificacao** | Grace Blackwell Workstation (NAO e Jetson) |

## 1.2 Software

| Software | Versao | Status |
|----------|--------|--------|
| **OS** | Ubuntu 24.04.3 LTS (Noble Numbat) | OK |
| **Kernel** | 6.14.0-1015-nvidia (PREEMPT_DYNAMIC) | OK - otimizado NVIDIA |
| **Python** | 3.12.3 | OK |
| **CUDA Toolkit** | 13.0.88 (nvcc) | OK |
| **PyTorch** | 2.10.0+cpu | PROBLEMA - CPU-only! |
| **Docker** | 28.5.1 | OK |
| **Docker Compose** | v2.40.0 | OK |
| **NVIDIA Container Toolkit** | 1.18.1 | OK |
| **Node.js** | v24.13.0 | OK |
| **npm** | 11.6.2 | OK |
| **FFmpeg** | 6.1.1 | OK - completo |
| **Rubberband** | Instalado | OK |
| **Ollama** | 0.15.2 | OK - rodando na GPU |
| **yt-dlp** | 2026.2.4 | OK |

## 1.3 Problema Critico: PyTorch CPU-Only

**Diagnostico:**
- PyTorch instalado via pip padrao: `torch==2.10.0+cpu`
- ARM64 nao tem wheels oficiais com CUDA no PyPI
- GPU GB10 (Blackwell) e muito nova, suporte limitado

**Solucao Confirmada:**
O container NVIDIA `nvcr.io/nvidia/pytorch:25.01-py3` funciona:
```
PyTorch: 2.6.0a0+ecf3bae40a.nv25.01
CUDA: True
CUDA version: 12.8
GPU: NVIDIA GB10
```

**Impacto da falta de GPU:**
- Bark TTS: ~50s/segmento (CPU) vs ~2s/segmento (GPU) = **25x mais lento**
- Whisper large-v3: ~40min para 1h de video (CPU) vs ~5min (GPU) = **8x mais lento**
- M2M100 traducao: ~30s/batch (CPU) vs ~3s/batch (GPU) = **10x mais lento**

## 1.4 Uso de GPU Atual

```
GPU NVIDIA GB10:
  - Ollama: 41,109 MB (qwen2.5:14b)
  - Xorg: 27 MB
  - gnome-shell: 17 MB
  - Pipeline: 0 MB (roda em CPU!)
  - Temperatura: 63-64C
  - Power: 14-15W (idle)
```

## 1.5 Portas Disponiveis

| Porta | Servico | Status |
|-------|---------|--------|
| 11434 | Ollama API | Em uso |
| 3000 | (Web frontend) | LIVRE |
| 5000 | (alternativa) | LIVRE |
| 8000 | (API backend) | LIVRE |
| 8080 | (alternativa) | LIVRE |
| 22 | SSH | Em uso |
| 3389 | RDP | Em uso |

---

# PARTE 2: ANALISE DO PROJETO

## 2.1 Visao Geral

**inemaVOX (base Dublar Pro v4.0.0)** - Suite de voz com IA para processamento de videos

- **Arquivo principal**: `dublar_pro_v4.py` (3042 linhas)
- **Versao anterior**: `dublar_pro.py` (v3.0)
- **Scripts auxiliares**: `dublar-pro.sh`, `instalar.sh`, `baixar-e-cortar.sh`
- **Diretorio de trabalho**: `dub_work/`
- **Diretorio de saida**: `dublado/`

## 2.2 Pipeline de 10 Etapas

```
1. Validacao e Download (YouTube/arquivo local)
   ↓
2. Extracao de Audio (FFmpeg → WAV 48kHz mono)
   ↓
3. Transcricao ASR (Faster-Whisper ou NVIDIA Parakeet)
   ↓
4. Traducao (M2M100 ou Ollama/LLM com contexto)
   ↓
5. Split de Segmentos (dividir frases longas)
   ↓
6. Sintese TTS (Edge/Bark/XTTS/Piper)
   ↓
7. Fade (fade-in/out suave)
   ↓
8. Sincronizacao (smart/fit/pad/extend)
   ↓
9. Concatenacao + Pos-processamento
   ↓
10. Mux Final (video + audio → MP4)
```

## 2.3 Motores Disponiveis

### ASR (Transcricao)

| Motor | Modelos | Idiomas | GPU | Offline |
|-------|---------|---------|-----|---------|
| **Faster-Whisper** (padrao) | tiny, small, medium, large, large-v3 | 99+ | Sim (CTranslate2) | Sim |
| **NVIDIA Parakeet** | tdt-1.1b, ctc-1.1b, rnnt-1.1b | Ingles apenas | Sim (NeMo) | Sim |

### Traducao

| Motor | Modelos | Qualidade | GPU | Offline |
|-------|---------|-----------|-----|---------|
| **M2M100** (padrao) | 418M, 1.2B | Boa/Muito boa | Sim | Sim |
| **Ollama/LLM** | qwen2.5:14b, llama3, etc | Excelente (com contexto) | Sim (Ollama) | Sim |

**Diferenciais da traducao:**
- Protecao de termos tecnicos (150+ termos preservados)
- Dicionario de correcoes (100+ correcoes automaticas)
- Glossario tecnico PT-EN
- CPS adaptativo (ajusta texto ao timing original)
- Contexto de 3-5 segmentos anteriores (Ollama)

### TTS (Sintese de Voz)

| Motor | Vozes PT-BR | GPU | Offline | Qualidade |
|-------|-------------|-----|---------|-----------|
| **Edge TTS** (padrao) | AntonioNeural, FranciscaNeural, ThalitaNeural | Nao precisa | Nao | Excelente |
| **Bark** | v2/pt_speaker_0 a 9 | Recomendado | Sim | Boa |
| **XTTS** (clone) | Clona voz original | Recomendado | Sim | Muito boa |
| **Piper** | pt_BR-faber-medium | Nao precisa | Sim | Razoavel |

### Sincronizacao

| Modo | Descricao | Melhor para |
|------|-----------|-------------|
| **smart** (padrao) | Pad se curto, fit se dentro do limite, trunca se muito longo | Uso geral |
| **fit** | Comprime/estica para caber no tempo | Videos sem demo |
| **pad** | Adiciona silencio ou corta | Simples |
| **extend** | Congela frame do video quando audio e mais longo | Demos/tutoriais |
| **none** | Sem sincronizacao | Testes |

## 2.4 Argumentos de Linha de Comando

### Entrada/Saida
```
--in VIDEO          Video de entrada ou URL YouTube (obrigatorio)
--src LANG          Idioma de origem (auto-detect se omitido)
--tgt LANG          Idioma de destino (obrigatorio)
--out VIDEO         Video de saida
--outdir DIR        Diretorio de saida (default: dublado/)
```

### Traducao
```
--tradutor ENGINE   ollama ou m2m100 (default: m2m100)
--modelo MODEL      Modelo Ollama (default: qwen2.5:14b)
--large-model       Usar M2M100 1.2B (melhor qualidade)
```

### TTS
```
--tts ENGINE        edge, bark, piper, xtts (default: edge)
--voice VOICE       Voz especifica
--rate RATE         Velocidade Edge TTS (default: +0%)
--texttemp FLOAT    Bark text temperature (default: 0.7)
--wavetemp FLOAT    Bark wave temperature (default: 0.5)
--max-retries N     Tentativas TTS (default: 2)
--clonar-voz        Clonar voz original com XTTS
```

### ASR
```
--asr ENGINE        whisper ou parakeet (default: whisper)
--whisper-model M   tiny, small, medium, large, large-v3 (default: large-v3)
--parakeet-model M  tdt-1.1b, ctc-1.1b, rnnt-1.1b
--segment-pause F   Pausa para novo segmento em segundos (default: 0.3)
--segment-max-words Maximo palavras por segmento (default: 15)
```

### Sincronizacao
```
--sync MODE         none, fit, pad, smart, extend (default: smart)
--tolerance FLOAT   Tolerancia de sync (default: 0.1 = 10%)
--maxstretch FLOAT  Compressao maxima (default: 1.3 = 30%)
--no-rubberband     Usar ffmpeg atempo ao inves de rubberband
--no-truncate       Nao truncar frases para timing
```

### Diarizacao
```
--diarize           Detectar multiplos falantes
--num-speakers N    Numero de falantes (auto se omitido)
```

### Qualidade
```
--qualidade PRESET  rapido, balanceado, maximo
--maxdur FLOAT      Duracao maxima por segmento (default: 10s)
--rate-audio INT    Sample rate de saida (default: 24000)
--bitrate STR       Bitrate AAC (default: 192k)
--fade 0|1          Aplicar fade (default: 1)
--seed INT          Seed para reproducibilidade (default: 42)
```

## 2.5 Presets de Qualidade

| Preset | ASR | Traducao | TTS | Extra |
|--------|-----|----------|-----|-------|
| **rapido** | Whisper small | M2M100 418M | Edge TTS | - |
| **balanceado** | Whisper large-v3 | M2M100 418M | Edge TTS | - |
| **maximo** | Whisper large-v3 | Ollama | Edge/XTTS | + diarizacao |

## 2.6 Sistema de Checkpoint

O pipeline salva progresso em `dub_work/checkpoint.json`:
```json
{
  "version": "4.0.0",
  "last_step": "transcription",
  "last_step_num": 3,
  "next_step": 4,
  "timestamp": "2026-02-09T01:22:10.673604",
  "data": {}
}
```

Se o processo for interrompido, pode ser retomado da ultima etapa salva.

## 2.7 Arquivos Gerados

| Arquivo | Descricao |
|---------|-----------|
| `dub_work/audio_src.wav` | Audio extraido do video original |
| `dub_work/asr.json` | Transcricao original (JSON com timestamps) |
| `dub_work/asr.srt` | Legendas originais (formato SRT) |
| `dub_work/asr_trad.json` | Traducao com metadados |
| `dub_work/asr_trad.srt` | Legendas traduzidas (formato SRT) |
| `dub_work/seg_XXXX.wav` | Segmentos de audio TTS |
| `dub_work/segments.csv` | Metricas por segmento |
| `dub_work/dub_raw.wav` | Audio concatenado |
| `dub_work/dub_final.wav` | Audio pos-processado |
| `dub_work/checkpoint.json` | Ponto de salvamento |
| `dub_work/logs.json` | Log completo da execucao |
| `dub_work/quality_metrics.json` | Metricas de qualidade |
| `dublado/video_dublado.mp4` | **VIDEO FINAL DUBLADO** |

## 2.8 Dependencias

### Python (requirements.txt)
- torch, transformers, faster-whisper
- edge-tts, bark
- scipy, numpy, librosa, soundfile
- sentencepiece, protobuf, sacremoses
- httpx (Ollama client)
- yt-dlp, Pillow

### Sistema
- ffmpeg (obrigatorio)
- rubberband-cli (opcional, melhor time-stretch)

### Opcionais
- ollama (LLM local para traducao)
- pyannote.audio (diarizacao de falantes)
- gradio (interface web - nao implementado)
- nemo_toolkit[asr] (NVIDIA Parakeet)

---

# PARTE 3: PROBLEMAS IDENTIFICADOS E SOLUCOES

## 3.1 PyTorch CPU-Only (CRITICO)

**Problema**: PyTorch instalado sem suporte CUDA no ARM64
**Impacto**: Pipeline 10-25x mais lento que o potencial da maquina
**Solucao**: Usar container Docker NVIDIA (`nvcr.io/nvidia/pytorch:25.01-py3`)
**Status**: Testado e confirmado funcionando com GB10

## 3.2 Sem Interface Web

**Problema**: Apenas CLI, dificil de usar e monitorar
**Impacto**: Nao permite monitorar progresso, dificil para nao-tecnicos
**Solucao**: Criar interface web com FastAPI (backend) + Next.js (frontend)
**Funcionalidades planejadas**:
- Formulario com todas opcoes de dublagem
- Monitor de progresso em tempo real (WebSocket)
- Selecao de modelos LLM/TTS/ASR
- Player de video para resultado
- Historico de jobs

## 3.3 dublar-pro.sh aponta para versao antiga

**Problema**: O script shell executa `dublar_pro.py` (v3) ao inves de `dublar_pro_v4.py`
**Solucao**: Atualizar referencia no script

## 3.4 venv sem ativacao no script

**Problema**: `dublar-pro.sh` nao ativa o ambiente virtual
**Solucao**: Adicionar ativacao do venv ou usar Docker

## 3.5 GPU compartilhada com Ollama

**Problema**: Ollama usa 41GB VRAM, pode conflitar com pipeline
**Solucao**:
- Gerenciamento automatico: descarregar modelo Ollama antes de TTS GPU
- API de controle: `ollama stop` antes, `ollama run` depois
- Backend web gerencia automaticamente

---

# PARTE 4: BENCHMARKS ESTIMADOS

## Com GPU (via Docker):

| Etapa | Video 10min | Video 1h |
|-------|-------------|----------|
| Download YouTube | 30s | 2min |
| Extracao audio | 2s | 10s |
| Whisper large-v3 | 1-2min | 5-8min |
| Traducao M2M100 | 30s | 3min |
| Edge TTS | 2min | 10min |
| Bark TTS (GPU) | 3min | 15min |
| Sync + Mux | 1min | 5min |
| **TOTAL Edge** | **~5min** | **~25min** |
| **TOTAL Bark GPU** | **~8min** | **~35min** |

## Sem GPU (atual, CPU):

| Etapa | Video 10min | Video 1h |
|-------|-------------|----------|
| Whisper large-v3 | 10-15min | 40-60min |
| Bark TTS (CPU) | 30-60min | 3-6 HORAS |
| **TOTAL Bark CPU** | **~1h** | **~5-7h** |

**Speedup com GPU: 5-10x**

---

# PARTE 5: ARQUITETURA PROPOSTA

## Diagrama

```
┌─────────────────────────────────────────────────┐
│                  USUARIO                         │
│         (Browser: localhost:3000)                 │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│            FRONTEND (Next.js)                    │
│  - Formulario de dublagem                        │
│  - Monitor de progresso (WebSocket)              │
│  - Player de video                               │
│  - Dashboard de sistema                          │
│  - Deploy: localhost:3000 ou Vercel              │
└─────────────────┬───────────────────────────────┘
                  │ REST API + WebSocket
                  ▼
┌─────────────────────────────────────────────────┐
│            BACKEND (FastAPI)                     │
│  - API REST (jobs, models, system)               │
│  - WebSocket (progresso em tempo real)           │
│  - Job Manager (fila, subprocess)                │
│  - Model Manager (Ollama, TTS, ASR)              │
│  - System Monitor (GPU, CPU, RAM)                │
│  - Deploy: localhost:8000 (Docker com GPU)       │
└──────┬─────────────┬────────────────────────────┘
       │             │
       ▼             ▼
┌──────────┐  ┌──────────────────────┐
│  Ollama  │  │  Pipeline Dublagem   │
│  :11434  │  │  (dublar_pro_v4.py)  │
│          │  │                      │
│ Models:  │  │  Whisper → Traducao  │
│ qwen2.5  │  │  → TTS → Sync → Mux │
│ llama3   │  │                      │
│ etc.     │  │  GPU via Docker      │
└──────────┘  └──────────────────────┘
```

---

# PARTE 6: IDIOMAS SUPORTADOS

| Codigo | Idioma | CPS | Vozes Edge TTS |
|--------|--------|-----|----------------|
| pt, pt-br | Portugues Brasil | 14 | Antonio, Francisca, Thalita |
| en, en-us | Ingles | 12 | Guy, Jenny, Aria |
| es, es-es | Espanhol | 13 | Alvaro, Elvira |
| es-mx | Espanhol Mexico | 13 | Jorge |
| fr | Frances | 13 | Henri, Denise |
| de | Alemao | 12 | Conrad, Katja |
| it | Italiano | 13 | Diego, Elsa |
| ja | Japones | 8 | Keita, Nanami |
| zh | Chines | 6 | Yunyang, Xiaoxiao |
| ko | Coreano | 9 | InJoon, SunHi |
| ru | Russo | 12 | Dmitry, Svetlana |
| ar | Arabe | 11 | Hamed, Zariyah |
| hi | Hindi | 12 | Madhur, Swara |

---

# PARTE 7: COMANDOS UTEIS

```bash
# Dublagem basica
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt

# YouTube para portugues
python dublar_pro_v4.py --in "https://youtube.com/watch?v=XXX" --tgt pt

# Qualidade maxima com Ollama
python dublar_pro_v4.py --in video.mp4 --tgt pt --qualidade maximo

# Com GPU via Docker
docker run --rm --gpus all --ipc=host \
  -v $(pwd):/app dublar-pro:gpu \
  --in video.mp4 --src en --tgt pt --tts bark

# Verificar GPU no container
docker run --rm --gpus all nvcr.io/nvidia/pytorch:25.01-py3 \
  python -c "import torch; print(torch.cuda.is_available())"
```

---

*Relatorio gerado em 2026-02-09 por Claude Code*
*Projeto: dublar4 (Dublar Pro v4.0.0)*
*Maquina: Grace Blackwell Workstation (NVIDIA GB10 + ARM64)*
