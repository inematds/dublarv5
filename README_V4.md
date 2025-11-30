# Dublar Pro v4.0

Pipeline profissional de dublagem automatica de videos.

## Novidades v4

| Feature | Descricao |
|---------|-----------|
| **Auto-deteccao idioma** | Whisper detecta idioma origem automaticamente |
| **Traducao com contexto** | Mantém consistência entre segmentos |
| **CPS adaptativo** | Ajusta texto baseado no ritmo original |
| **Download YouTube** | Baixa video direto da URL |
| **Clonagem de voz** | XTTS replica voz do video original |
| **Diarizacao** | Detecta multiplos falantes |
| **Edge TTS padrao** | Vozes consistentes da Microsoft |
| **Ollama** | Traducao natural via LLM local |

## Instalacao

```bash
# Dependencias basicas
pip install -r requirements.txt

# Opcional: Ollama para traducao natural
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3

# Opcional: FFmpeg e Rubberband
sudo apt install ffmpeg rubberband-cli
```

## Uso Basico

```bash
# Video local (auto-detectar idioma origem)
python dublar_pro_v4.py --in video.mp4 --tgt pt

# Video local (idioma especificado)
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt

# URL do YouTube
python dublar_pro_v4.py --in "https://youtube.com/watch?v=XXX" --tgt pt
```

## Presets de Qualidade

```bash
# Rapido (Edge + M2M100 + Whisper small)
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --qualidade rapido

# Balanceado (Edge + M2M100 + Whisper medium) - PADRAO
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --qualidade balanceado

# Maximo (Edge/XTTS + Ollama + Whisper large + diarizacao)
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --qualidade maximo
```

## Exemplos Avancados

```bash
# Traducao via Ollama (mais natural)
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --tradutor ollama --modelo llama3

# Clonar voz do video original
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --clonar-voz

# Multiplos falantes (diarizacao)
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --diarize

# Voz especifica + velocidade
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --voice pt-BR-FranciscaNeural --rate "+10%"

# Bark TTS (offline)
python dublar_pro_v4.py --in video.mp4 --src en --tgt pt --tts bark --voice v2/pt_speaker_3
```

## Parametros

### Entrada/Saida
| Parametro | Descricao | Default |
|-----------|-----------|---------|
| `--in` | Video ou URL YouTube | (obrigatorio) |
| `--src` | Idioma origem | auto-detectar |
| `--tgt` | Idioma destino | (obrigatorio) |
| `--out` | Arquivo de saida | auto |
| `--outdir` | Diretorio de saida | dublado/ |

### Traducao
| Parametro | Descricao | Default |
|-----------|-----------|---------|
| `--tradutor` | ollama, m2m100 | m2m100 |
| `--modelo` | Modelo Ollama | llama3 |
| `--large-model` | M2M100 1.2B | False |

### TTS
| Parametro | Descricao | Default |
|-----------|-----------|---------|
| `--tts` | edge, bark, piper, xtts | edge |
| `--voice` | Voz especifica | auto |
| `--rate` | Velocidade Edge | +0% |
| `--clonar-voz` | Clonar voz original | False |

### Whisper
| Parametro | Descricao | Default |
|-----------|-----------|---------|
| `--whisper-model` | tiny, small, medium, large | medium |
| `--diarize` | Detectar falantes | False |
| `--num-speakers` | Numero de falantes | auto |

### Sincronizacao
| Parametro | Descricao | Default |
|-----------|-----------|---------|
| `--sync` | none, fit, pad, smart | smart |
| `--tolerance` | Tolerancia % | 0.1 |
| `--maxstretch` | Max compressao | 2.0 |
| `--use-rubberband` | Usar rubberband | False |

## Vozes Edge TTS

### Portugues Brasil
- `pt-BR-AntonioNeural` (masculina, padrao)
- `pt-BR-FranciscaNeural` (feminina)
- `pt-BR-ThalitaNeural` (feminina)

### Ingles
- `en-US-GuyNeural` (masculina)
- `en-US-JennyNeural` (feminina)
- `en-US-AriaNeural` (feminina)

### Espanhol
- `es-ES-AlvaroNeural` (masculina)
- `es-ES-ElviraNeural` (feminina)
- `es-MX-JorgeNeural` (masculina, Mexico)

## Vozes Bark

- `v2/pt_speaker_0` a `v2/pt_speaker_9`
- `v2/en_speaker_0` a `v2/en_speaker_9`

## Arquitetura

```
Video -> FFmpeg -> Whisper -> Traducao -> TTS -> Sync -> Mux -> Video dublado
           |          |          |         |       |
         Audio     Texto     Texto PT   Audios  Ajustados
```

## Estrutura de Saida

```
dublado/
  video_dublado.mp4     # Video final

dub_work/
  audio_src.wav         # Audio extraido
  asr.srt               # Transcricao original
  asr_trad.srt          # Traducao
  segments.csv          # Metricas por segmento
  seg_0001.wav          # Audios TTS
  quality_metrics.json  # Metricas finais
  logs.json             # Log completo
  checkpoint.json       # Para retomar
```

## Testar Instalacao

```bash
python test_v4.py
```

## Troubleshooting

### Edge TTS nao funciona
```bash
pip install --upgrade edge-tts
```

### Ollama nao conecta
```bash
ollama serve  # Em outro terminal
```

### XTTS erro Python 3.12+
XTTS requer Python < 3.12. Use Edge TTS como alternativa.

### Memoria insuficiente
```bash
# Usar modelos menores
--whisper-model small
--tradutor m2m100  # em vez de ollama
--tts edge  # em vez de bark
```

## Requisitos

- Python 3.9+
- FFmpeg
- 4GB+ RAM
- GPU opcional (acelera Whisper e Bark)

## Licenca

MIT
