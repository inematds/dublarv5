# inemaVOX - Dublar Video

Traduz e dubla automaticamente qualquer video usando IA local. O pipeline cobre desde o download do video ate a mixagem final com audio dublado sincronizado.

---

## Como funciona

O pipeline executa **10 etapas** dentro de um container Docker com GPU:

```
Video/URL
   │
   ▼
1. Download          → yt-dlp (YouTube, TikTok, Instagram...)
2. Extrair audio     → ffmpeg
3. Transcrever (ASR) → Whisper large-v3 / Parakeet 1.1B
4. Traduzir          → M2M100 (offline) / Ollama (LLM local)
5. Dividir segmentos → ffmpeg
6. Sintetizar voz    → Edge TTS / Bark / XTTS / Piper
7. Sincronizar       → rubberband (stretch/compress por segmento)
8. Concatenar        → ffmpeg
9. Pos-processar     → normalizacao de volume, filtros
10. Mux final        → video original + audio dublado
   │
   ▼
video_dublado.mp4
```

---

## Interface Web (`/new`)

1. Acesse `http://localhost:3000/new`
2. Cole a URL do video **ou** arraste um arquivo local
3. Configure os parametros:
   - **Idioma de origem**: auto-detect ou especifique (ex: `en`, `es`, `ja`)
   - **Idioma de destino**: ex: `pt` para Portugues Brasileiro
   - **Motor TTS**: veja tabela abaixo
   - **Motor de traducao**: M2M100 (rapido, offline) ou Ollama (melhor qualidade)
   - **Modelo Whisper**: recomendado `large-v3` para maxima qualidade
4. Clique em **Dublar** e acompanhe o progresso etapa por etapa

---

## CLI (`dublar_pro_v5.py`)

```bash
# Dublar video do YouTube para Portugues
python dublar_pro_v5.py \
  --in "https://www.youtube.com/watch?v=VIDEO_ID" \
  --tgt pt \
  --tts edge \
  --tradutor m2m100 \
  --whisper-model large-v3

# Dublar arquivo local com Bark (GPU, alta qualidade)
python dublar_pro_v5.py \
  --in video.mp4 \
  --tgt pt \
  --tts bark \
  --tradutor ollama \
  --modelo qwen2.5:14b \
  --outdir ./resultado

# Clonar voz original (XTTS)
python dublar_pro_v5.py \
  --in video.mp4 \
  --tgt pt \
  --tts xtts \
  --clonar-voz \
  --outdir ./resultado

# Com diarizacao (multiplos falantes)
python dublar_pro_v5.py \
  --in podcast.mp4 \
  --tgt pt \
  --tts edge \
  --diarize \
  --outdir ./resultado
```

### Parametros

| Parametro | Descricao | Opcoes | Default |
|-----------|-----------|--------|---------|
| `--in` | Video ou URL | arquivo local, URL YouTube/TikTok/etc | obrigatorio |
| `--tgt` | Idioma destino | `pt`, `en`, `es`, `fr`, `de`, `ja`, `zh`... | obrigatorio |
| `--src` | Idioma origem | `auto`, `en`, `es`, `ja`... | `auto` |
| `--tts` | Motor de voz | `edge`, `bark`, `xtts`, `piper` | `edge` |
| `--voice` | Voz especifica | ex: `pt-BR-FranciscaNeural` | auto |
| `--tradutor` | Motor de traducao | `m2m100`, `ollama` | `m2m100` |
| `--modelo` | Modelo Ollama | `qwen2.5:14b`, `llama3.1:8b`... | `qwen2.5:14b` |
| `--asr` | Motor de transcricao | `whisper`, `parakeet` | `whisper` |
| `--whisper-model` | Tamanho do Whisper | `tiny`, `small`, `medium`, `large`, `large-v3` | `large-v3` |
| `--sync` | Modo de sincronizacao | `none`, `fit`, `pad`, `smart`, `extend` | `smart` |
| `--maxstretch` | Fator maximo de stretch | `1.0` a `2.0` | `1.3` |
| `--diarize` | Detectar multiplos falantes | flag (sem valor) | desativado |
| `--clonar-voz` | Clonar voz original (XTTS) | flag (sem valor) | desativado |
| `--outdir` | Diretorio de saida | qualquer path | `./dublado` |
| `--seed` | Seed para reproducibilidade | inteiro | `42` |

---

## Motores TTS

| Motor | GPU | Internet | Qualidade | Velocidade | Notas |
|-------|-----|----------|-----------|------------|-------|
| **Edge TTS** | Nao | Sim | Boa | Muito rapido | Microsoft neural voices; requer conexao |
| **Bark** | Sim | Nao | Alta | Rapido (GPU) | Expressivo, suporta emocoes |
| **XTTS** | Sim | Nao | Alta + clone | Medio | Clona a voz do falante original |
| **Piper** | Nao | Nao | Media | Muito rapido | Leve, ideal para CPU |

### Vozes Edge TTS disponiveis (exemplos)

| Idioma | Vozes |
|--------|-------|
| Portugues BR | `pt-BR-FranciscaNeural` (F), `pt-BR-AntonioNeural` (M) |
| Portugues PT | `pt-PT-RaquelNeural` (F), `pt-PT-DuarteNeural` (M) |
| Ingles | `en-US-JennyNeural`, `en-US-GuyNeural` |
| Espanhol | `es-ES-ElviraNeural`, `es-MX-DaliaNeural` |

---

## Motores de Traducao

| Motor | GPU | Internet | Qualidade | Notas |
|-------|-----|----------|-----------|-------|
| **M2M100 418M** | Opcional | Nao | Boa | Rapido, modelo menor |
| **M2M100 1.2B** | Recomendado | Nao | Muito boa | Padrao recomendado |
| **Ollama** | Sim | Nao | Excelente | Depende do modelo; usa contexto |

> **Dica:** Ollama com `qwen2.5:14b` produz a melhor qualidade de traducao, especialmente para contextos tecnicos e linguagem coloquial.

---

## Modos de Sincronizacao

| Modo | Descricao | Quando usar |
|------|-----------|-------------|
| `smart` | Ajusta automaticamente (stretch + padding) | Padrao para maioria dos casos |
| `fit` | Estica/comprime o audio para caber exatamente | Boa sincronia labial |
| `pad` | Adiciona silencio ao final se o audio for curto | Preserva timbre natural |
| `extend` | Estica apenas, nunca corta | Vozes sensiveis a compressao |
| `none` | Sem sincronizacao | Debug / testes |

---

## Saida

```
outdir/
├── video_dublado.mp4     # Video final com audio dublado
├── subs_original.srt     # Legendas no idioma original
└── subs_traduzido.srt    # Legendas traduzidas
```

O resultado fica disponivel no job detail (`/jobs/{id}`) com:
- Player inline do video dublado
- Titulo do video detectado automaticamente
- Download do MP4 e das legendas SRT

---

## Via API

```bash
# Dublar por URL
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "input": "https://www.youtube.com/watch?v=VIDEO_ID",
    "tgt_lang": "pt",
    "tts_engine": "edge",
    "translation_engine": "m2m100",
    "whisper_model": "large-v3",
    "sync_mode": "smart"
  }'

# Dublar com upload de arquivo
curl -X POST http://localhost:8000/api/jobs/upload \
  -F "file=@video.mp4" \
  -F 'config_json={"tgt_lang":"pt","tts_engine":"edge","translation_engine":"m2m100"}'
```

---

## Dicas

- Use `large-v3` para idiomas com sotaque forte ou audio com ruido
- Para videos com multiplos falantes, ative `--diarize`
- Se o audio dublado ficar fora de sincronia, tente `--sync fit` ou reduza `--maxstretch 1.1`
- M2M100 e totalmente offline; Ollama requer o servico rodando em `localhost:11434`
- Parakeet so funciona com audio em ingles; use Whisper para outros idiomas
