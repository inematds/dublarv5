# Transcrever Video

Gera legendas e transcricoes a partir de qualquer video ou audio usando modelos de reconhecimento de fala (ASR) com GPU. Suporta dezenas de idiomas e exporta nos formatos SRT, TXT e JSON.

---

## Como funciona

O pipeline executa **4 etapas**:

```
Video/URL
   │
   ▼
1. Download/preparar  → yt-dlp ou arquivo local
2. Extrair audio      → ffmpeg (converte para WAV mono 16kHz)
3. Transcrever (ASR)  → Whisper / Parakeet
4. Exportar legendas  → SRT + TXT + JSON
   │
   ▼
transcript.srt / transcript.txt / transcript.json
```

---

## Interface Web (`/transcribe`)

1. Acesse `http://localhost:3000/transcribe`
2. Cole a URL do video **ou** arraste um arquivo local
3. Configure:
   - **Motor ASR**: Whisper (multiplos idiomas) ou Parakeet (ingles, muito rapido)
   - **Modelo Whisper**: de `tiny` (rapido) a `large-v3` (maxima qualidade)
   - **Idioma**: auto-detect ou especifique para maior precisao
4. Clique em **Transcrever** e acompanhe o progresso
5. Ao concluir, faca download nos formatos desejados (SRT / TXT / JSON)

---

## CLI (`transcrever_v1.py`)

```bash
# Transcrever video local com Whisper large-v3
python transcrever_v1.py \
  --in video.mp4 \
  --outdir ./transcription \
  --asr whisper \
  --whisper-model large-v3

# Transcrever URL com idioma definido
python transcrever_v1.py \
  --in "https://www.youtube.com/watch?v=VIDEO_ID" \
  --outdir ./transcription \
  --asr whisper \
  --whisper-model large-v3 \
  --src en

# Transcrever ingles com Parakeet (mais rapido)
python transcrever_v1.py \
  --in podcast.mp4 \
  --outdir ./transcription \
  --asr parakeet
```

### Parametros

| Parametro | Descricao | Opcoes | Default |
|-----------|-----------|--------|---------|
| `--in` | Video, audio ou URL | arquivo local, URL YouTube/TikTok/etc | obrigatorio |
| `--outdir` | Diretorio de saida | qualquer path | obrigatorio |
| `--asr` | Motor de transcricao | `whisper`, `parakeet` | `whisper` |
| `--whisper-model` | Tamanho do modelo Whisper | `tiny`, `small`, `medium`, `large`, `large-v3` | `large-v3` |
| `--src` | Idioma do audio | `auto`, `en`, `pt`, `es`, `ja`, `zh`... | auto-detect |

---

## Modelos ASR

| Motor | GPU | Idiomas | Velocidade | Qualidade | Notas |
|-------|-----|---------|------------|-----------|-------|
| Whisper tiny | Opcional | 99 | Muito rapido | Basica | Para testes e demos |
| Whisper small | Opcional | 99 | Rapido | Boa | Boa opcao para CPU |
| Whisper medium | Opcional | 99 | Medio | Muito boa | Equilibrio qualidade/velocidade |
| Whisper large-v3 | Recomendado | 99 | Medio (GPU) | Excelente | Padrao recomendado |
| Parakeet 1.1B | Sim | **So ingles** | Muito rapido | Alta | NVIDIA, ideal para podcasts em ingles |

> **Referencia de tempo** com GPU Blackwell (GB10): video de 10 minutos com `large-v3` → ~2-3 minutos.

---

## Formatos de Saida

### SRT (Legendas)
Formato padrao para players e editores de video:
```
1
00:00:01,240 --> 00:00:04,580
Texto do primeiro segmento da transcricao.

2
00:00:04,820 --> 00:00:08,140
Texto do segundo segmento.
```

### TXT (Texto plano)
Transcricao corrida sem timecodes, ideal para leitura e processamento:
```
Texto do primeiro segmento da transcricao. Texto do segundo segmento.
```

### JSON (Dados brutos)
Formato completo com todos os metadados por segmento:
```json
[
  {
    "start": 1.24,
    "end": 4.58,
    "text": "Texto do primeiro segmento.",
    "words": [...]
  }
]
```

---

## Saida no Job Detail

Ao concluir, a pagina `/jobs/{id}` exibe:
- **Titulo e preview** da transcricao (gerado automaticamente dos primeiros segmentos)
- Botoes de download para **SRT**, **TXT** e **JSON**

---

## Via API

```bash
# Transcrever por URL
curl -X POST http://localhost:8000/api/jobs/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "input": "https://www.youtube.com/watch?v=VIDEO_ID",
    "asr_engine": "whisper",
    "whisper_model": "large-v3"
  }'

# Transcrever com upload de arquivo
curl -X POST http://localhost:8000/api/jobs/transcribe/upload \
  -F "file=@video.mp4" \
  -F 'config_json={"asr_engine":"whisper","whisper_model":"large-v3","src_lang":"pt"}'

# Baixar resultado em SRT
curl http://localhost:8000/api/jobs/{JOB_ID}/transcript?format=srt -o legendas.srt

# Baixar resultado em TXT
curl http://localhost:8000/api/jobs/{JOB_ID}/transcript?format=txt -o transcricao.txt

# Baixar resultado em JSON
curl http://localhost:8000/api/jobs/{JOB_ID}/transcript?format=json -o dados.json
```

---

## Idiomas Suportados (Whisper)

Whisper suporta 99 idiomas. Os mais comuns:

| Codigo | Idioma |
|--------|--------|
| `pt` | Portugues (BR e PT) |
| `en` | Ingles |
| `es` | Espanhol |
| `fr` | Frances |
| `de` | Alemao |
| `it` | Italiano |
| `ja` | Japones |
| `zh` | Chines |
| `ko` | Coreano |
| `ru` | Russo |
| `ar` | Arabe |
| `hi` | Hindi |

---

## Dicas

- Especifique `--src` quando souber o idioma: evita deteccao errada e melhora a precisao
- Para podcasts e entrevistas em ingles, Parakeet e significativamente mais rapido que Whisper
- O arquivo JSON contem timestamps por palavra (`words`), util para gerador de legendas animadas
- `large-v3` detecta automaticamente o idioma nos primeiros 30 segundos; audios curtos podem ter deteccao imprecisa
- Para audio com muito ruido ou sotaque forte, prefira `large-v3` ao `medium`
