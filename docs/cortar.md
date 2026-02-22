# Cortar Video

Extrai clips de um video por timestamps manuais ou deixa a IA identificar automaticamente os melhores momentos para viralizar. Ideal para criar highlights, recortes de podcasts, shorts e reels.

---

## Como funciona

### Modo Manual

```
Video + Timestamps ("00:30-02:15, 05:00-07:30")
   │
   ▼
ffmpeg recorta cada segmento sem reencoding (rapido)
   │
   ▼
clip_01.mp4, clip_02.mp4, ..., clips.zip
```

### Modo Viral (IA)

```
Video
   │
   ▼
1. Download/preparar  → yt-dlp ou arquivo local
2. Extrair audio      → ffmpeg
3. Transcrever        → Whisper large-v3
4. Analisar com LLM   → Ollama / OpenAI / Anthropic / Groq...
   (LLM recebe a transcricao completa e decide quais trechos sao mais envolventes)
5. Recortar clips     → ffmpeg
6. Empacotar          → clips.zip
   │
   ▼
clip_01.mp4 ... clip_N.mp4 + clips.zip
```

---

## Interface Web (`/cut`)

1. Acesse `http://localhost:3000/cut`
2. Cole a URL do video **ou** arraste um arquivo local
3. Escolha o modo:

### Modo Manual
- Informe os timestamps no formato `MM:SS-MM:SS` separados por virgula
- Exemplos: `00:30-02:15, 05:00-07:30, 10:00-12:45`
- Formatos aceitos: `SS`, `MM:SS`, `HH:MM:SS`

### Modo Viral (IA)
- Escolha o provider LLM e o modelo
- Configure o numero de clips e duracao minima/maxima
- O LLM analisa a transcricao e retorna os melhores momentos com titulo e descricao

4. Clique em **Cortar** e acompanhe o progresso
5. Ao concluir, assista cada clip no player inline e faca download individual ou em ZIP

---

## CLI (`clipar_v1.py`)

```bash
# Modo manual por timestamps
python clipar_v1.py \
  --in video.mp4 \
  --outdir ./clips \
  --mode manual \
  --timestamps "00:30-02:15, 05:00-07:30"

# Modo manual com URL
python clipar_v1.py \
  --in "https://www.youtube.com/watch?v=VIDEO_ID" \
  --outdir ./clips \
  --mode manual \
  --timestamps "01:00-03:30, 10:15-12:00"

# Modo viral com Ollama local
python clipar_v1.py \
  --in video.mp4 \
  --outdir ./clips \
  --mode viral \
  --ollama-model qwen2.5:7b \
  --num-clips 5 \
  --min-duration 30 \
  --max-duration 90

# Modo viral com OpenAI
python clipar_v1.py \
  --in video.mp4 \
  --outdir ./clips \
  --mode viral \
  --llm-provider openai \
  --llm-model gpt-4o \
  --llm-api-key sk-... \
  --num-clips 3

# Modo viral com Groq (rapido e gratuito)
python clipar_v1.py \
  --in podcast.mp4 \
  --outdir ./clips \
  --mode viral \
  --llm-provider groq \
  --llm-model llama-3.3-70b-versatile \
  --llm-api-key gsk_... \
  --num-clips 5 \
  --whisper-model large-v3
```

### Parametros

| Parametro | Descricao | Opcoes | Default |
|-----------|-----------|--------|---------|
| `--in` | Video ou URL | arquivo local, URL YouTube/TikTok/etc | obrigatorio |
| `--outdir` | Diretorio de saida | qualquer path | obrigatorio |
| `--mode` | Modo de corte | `manual`, `viral` | `manual` |
| `--timestamps` | Timestamps (modo manual) | `"HH:MM:SS-HH:MM:SS, ..."` | — |
| `--num-clips` | Numero de clips (modo viral) | inteiro | `5` |
| `--min-duration` | Duracao minima em segundos | inteiro | `30` |
| `--max-duration` | Duracao maxima em segundos | inteiro | `120` |
| `--ollama-model` | Modelo Ollama para analise | `qwen2.5:7b`, `llama3.1:8b`... | `qwen2.5:7b` |
| `--llm-provider` | Provider externo | `ollama`, `openai`, `anthropic`, `groq`, `deepseek`, `together`, `openrouter`, `custom` | `ollama` |
| `--llm-model` | Modelo do provider externo | ex: `gpt-4o`, `claude-3-5-sonnet` | — |
| `--llm-api-key` | API key do provider | string | — |
| `--llm-base-url` | URL base (provider custom) | URL | — |
| `--whisper-model` | Modelo Whisper para transcricao | `tiny`, `small`, `medium`, `large-v3` | `large-v3` |

---

## Formato de Timestamps

O parser aceita varios formatos e separadores:

```
# Formato MM:SS
00:30-02:15, 05:00-07:30

# Formato HH:MM:SS
01:00:00-01:05:30, 01:30:00-01:35:00

# Formato misto
30-135, 05:00-07:30, 01:00:00-01:05:00

# Separadores aceitos: virgula, ponto-e-virgula, nova linha
00:30-02:15; 05:00-07:30
00:30-02:15
05:00-07:30
```

---

## Providers LLM (Modo Viral)

| Provider | Parametro | Notas |
|----------|-----------|-------|
| Ollama (local) | `ollama` | Gratuito, sem internet, requer GPU |
| OpenAI | `openai` | `gpt-4o`, `gpt-4o-mini` |
| Anthropic | `anthropic` | `claude-3-5-sonnet-20241022` |
| Groq | `groq` | Rapido, tier gratuito disponivel |
| DeepSeek | `deepseek` | Custo muito baixo |
| Together | `together` | Vários modelos open-source |
| OpenRouter | `openrouter` | Acesso a muitos providers |
| Custom | `custom` | Qualquer API OpenAI-compativel com `--llm-base-url` |

---

## Saida

```
outdir/
├── clip_01.mp4    # Primeiro clip
├── clip_02.mp4    # Segundo clip
├── ...
├── clip_N.mp4
└── clips.zip      # Todos os clips em um ZIP
```

No modo viral, cada clip tem:
- **Titulo** gerado pelo LLM
- **Descricao** do momento (por que e relevante)
- **Timecodes** (inicio e fim)

Esses metadados aparecem na interface no job detail (`/jobs/{id}`).

---

## Via API

```bash
# Corte manual por URL
curl -X POST http://localhost:8000/api/jobs/cut \
  -H "Content-Type: application/json" \
  -d '{
    "input": "https://www.youtube.com/watch?v=VIDEO_ID",
    "mode": "manual",
    "timestamps": "00:30-02:15, 05:00-07:30"
  }'

# Corte viral com Ollama
curl -X POST http://localhost:8000/api/jobs/cut \
  -H "Content-Type: application/json" \
  -d '{
    "input": "https://www.youtube.com/watch?v=VIDEO_ID",
    "mode": "viral",
    "ollama_model": "qwen2.5:7b",
    "num_clips": 5,
    "min_duration": 30,
    "max_duration": 90,
    "whisper_model": "large-v3"
  }'

# Corte com upload de arquivo
curl -X POST http://localhost:8000/api/jobs/cut/upload \
  -F "file=@video.mp4" \
  -F 'config_json={"mode":"manual","timestamps":"00:30-02:15"}'

# Listar clips gerados
curl http://localhost:8000/api/jobs/{JOB_ID}/clips

# Download de clip individual
curl http://localhost:8000/api/jobs/{JOB_ID}/clips/clip_01.mp4 -o clip_01.mp4

# Download de todos em ZIP
curl http://localhost:8000/api/jobs/{JOB_ID}/clips/zip -o clips.zip
```

---

## Dicas

- No modo manual, o recorte e feito sem reencoding (copia de stream) — muito rapido independente da duracao do video
- No modo viral, a qualidade dos clips depende do LLM escolhido; modelos maiores identificam melhores momentos
- Para podcasts longos, use `--min-duration 60 --max-duration 180` para clips mais substanciais
- Para Shorts/Reels, use `--max-duration 60` para manter os clips dentro do limite de 1 minuto
- Groq com `llama-3.3-70b-versatile` oferece excelente qualidade com tier gratuito generoso
- Se o Ollama nao estiver rodando, inicie com `ollama serve` antes de criar o job
