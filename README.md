# Dublar - Sistema de Dublagem Automatica de Videos

Sistema de dublagem automatica usando IA para transcricao, traducao e sintese de voz.

## Caracteristicas

- **Transcricao automatica** com Whisper (faster-whisper)
- **Traducao** com M2M100 ou Ollama (LLM local)
- **Sintese de voz** com Edge TTS, Bark, Piper ou XTTS
- **Sincronizacao inteligente** com modos: none, fit, pad, smart
- **Download YouTube** direto da URL
- **Clonagem de voz** com XTTS
- **Deteccao de multiplos falantes** (diarizacao)
- **Suporte GPU** NVIDIA CUDA (opcional)

## Instalacao

### Linux

```bash
git clone https://github.com/inematds/dublar.git
cd dublar
chmod +x instalar.sh
./instalar.sh
source venv/bin/activate
```

### Dependencias opcionais

```bash
# Ollama para traducao natural
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3

# Rubberband para time-stretch
sudo apt install rubberband-cli
```

## Uso Basico

```bash
# Ativar ambiente
source venv/bin/activate

# Dublagem simples (auto-detecta idioma origem)
python dublar_pro_v4.py --in video.mp4 --tgt pt

# Especificar idioma origem
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt

# URL do YouTube
python dublar_pro_v4.py --in "https://youtube.com/watch?v=XXX" --tgt pt
```

## Presets de Qualidade

```bash
# Rapido (Edge + M2M100 + Whisper small)
python dublar_pro_v4.py --in video.mp4 --tgt pt --qualidade rapido

# Balanceado (padrao)
python dublar_pro_v4.py --in video.mp4 --tgt pt --qualidade balanceado

# Maximo (Ollama + Whisper large + diarizacao)
python dublar_pro_v4.py --in video.mp4 --tgt pt --qualidade maximo
```

## Exemplos Avancados

```bash
# Traducao via Ollama (mais natural)
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --tradutor ollama

# Clonar voz do video original
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --clonar-voz

# Multiplos falantes
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --diarize

# Voz especifica
python dublar_pro_v4.py --in video.mp4 --tgt pt --voice pt-BR-FranciscaNeural
```

## Parametros Principais

| Parametro | Descricao | Default |
|-----------|-----------|---------|
| `--in` | Video ou URL YouTube | obrigatorio |
| `--src` | Idioma origem | auto-detectar |
| `--tgt` | Idioma destino | obrigatorio |
| `--tts` | edge, bark, piper, xtts | edge |
| `--tradutor` | m2m100, ollama | m2m100 |
| `--sync` | none, fit, pad, smart | smart |
| `--whisper-model` | tiny, small, medium, large | medium |

## Vozes Disponiveis

### Edge TTS (padrao)
- `pt-BR-AntonioNeural` (masculina)
- `pt-BR-FranciscaNeural` (feminina)
- `en-US-GuyNeural` (masculina)
- `en-US-JennyNeural` (feminina)

### Bark (offline)
- `v2/pt_speaker_0` a `v2/pt_speaker_9`
- `v2/en_speaker_0` a `v2/en_speaker_9`

## Requisitos

- Python 3.9+
- FFmpeg
- 4GB+ RAM (8GB+ recomendado)
- GPU opcional (acelera Whisper e Bark)

## Estrutura do Projeto

```
dublar/
├── dublar_pro_v4.py   # Script principal (v4)
├── dublar_pro.py      # Versao anterior (v3)
├── dublar-pro.sh      # Launcher shell
├── instalar.sh        # Instalador Linux
├── requirements.txt   # Dependencias Python
├── venv/              # Ambiente virtual
├── dub_work/          # Arquivos temporarios (auto)
└── dublado/           # Videos finais (auto)
```

## Arquivos Gerados

```
dub_work/
├── audio_src.wav      # Audio extraido
├── asr.srt            # Transcricao original
├── asr_trad.srt       # Traducao
├── seg_*.wav          # Segmentos TTS
├── logs.json          # Log completo
└── checkpoint.json    # Para retomar

dublado/
└── video_dublado.mp4  # Resultado final
```

## Troubleshooting

### FFmpeg nao encontrado
```bash
sudo apt install ffmpeg
```

### Edge TTS nao funciona
```bash
pip install --upgrade edge-tts
```

### Memoria insuficiente
```bash
# Usar modelos menores
--whisper-model small --tts edge
```

### Forcar CPU
```bash
export CUDA_VISIBLE_DEVICES=""
python dublar_pro_v4.py ...
```

## Documentacao Adicional

- [INSTALL_LINUX.md](INSTALL_LINUX.md) - Guia de instalacao Linux
- [README_PRO.md](README_PRO.md) - Documentacao v3
- [README_V4.md](README_V4.md) - Documentacao v4

## Licenca

MIT
