# Baixar Video

Faz download de videos de +1000 sites usando yt-dlp. Suporta YouTube, TikTok, Instagram, Facebook, Twitter/X, Twitch e muitos outros. Escolha a qualidade desejada e o arquivo fica disponivel para download direto pela interface.

---

## Como funciona

```
URL do video
   │
   ▼
yt-dlp seleciona a melhor stream conforme qualidade escolhida
   │
   ▼
ffmpeg mescla video + audio (quando necessario)
   │
   ▼
video.mp4 (ou video.mp3 no modo audio)
```

---

## Interface Web (`/download`)

1. Acesse `http://localhost:3000/download`
2. Cole a URL do video
3. Escolha a qualidade:
   - **Melhor** — maxima qualidade disponivel (recomendado)
   - **1080p** — Full HD
   - **720p** — HD
   - **480p** — SD (menor arquivo)
   - **So Audio (MP3)** — extrai apenas o audio em MP3 192kbps
4. Clique em **Baixar** e acompanhe o progresso em tempo real (%, velocidade, ETA)
5. Ao concluir, assista no player inline ou clique em **Download** para salvar

---

## CLI (`baixar_v1.py`)

```bash
# Download na melhor qualidade
python baixar_v1.py \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --outdir ./downloads

# Download em 1080p
python baixar_v1.py \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --outdir ./downloads \
  --quality 1080p

# Extrair audio em MP3
python baixar_v1.py \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --outdir ./downloads \
  --quality audio

# Download do TikTok
python baixar_v1.py \
  --url "https://www.tiktok.com/@usuario/video/ID" \
  --outdir ./downloads

# Download do Instagram
python baixar_v1.py \
  --url "https://www.instagram.com/p/SHORTCODE/" \
  --outdir ./downloads
```

### Parametros

| Parametro | Descricao | Opcoes | Default |
|-----------|-----------|--------|---------|
| `--url` | URL do video | qualquer site suportado pelo yt-dlp | obrigatorio |
| `--outdir` | Diretorio de saida | qualquer path | obrigatorio |
| `--quality` | Qualidade desejada | `best`, `1080p`, `720p`, `480p`, `audio` | `best` |

---

## Qualidades Disponiveis

| Opcao | Resolucao | Formato | Notas |
|-------|-----------|---------|-------|
| `best` | Maxima disponivel | MP4 | Pode ser 4K se o site oferecer |
| `1080p` | 1920×1080 | MP4 | Full HD |
| `720p` | 1280×720 | MP4 | HD |
| `480p` | 854×480 | MP4 | SD |
| `audio` | — | MP3 192kbps | Apenas audio |

---

## Sites Suportados

yt-dlp suporta mais de 1000 sites. Os principais:

| Plataforma | Observacoes |
|-----------|-------------|
| YouTube | Videos, Shorts, lives (segmento ao vivo), playlists |
| TikTok | Videos publicos |
| Instagram | Posts, Reels (conta publica) |
| Facebook | Videos publicos |
| Twitter / X | Videos em tweets publicos |
| Twitch | VODs e clips |
| Vimeo | Videos publicos e com senha |
| Dailymotion | Videos publicos |
| Reddit | Videos hospedados no Reddit |
| SoundCloud | Audios (use `--quality audio`) |

> Para a lista completa: `python -m yt_dlp --list-extractors`

---

## Saida

```
outdir/
└── video.mp4    # (ou video.mp3 no modo audio)
```

O resultado fica disponivel no job detail (`/jobs/{id}`) com:
- Player inline do video baixado
- Botao de download direto

---

## Via API

```bash
# Criar job de download
curl -X POST http://localhost:8000/api/jobs/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "quality": "1080p"}'

# Resposta: {"id": "abc123", "status": "queued", ...}

# Acompanhar status
curl http://localhost:8000/api/jobs/abc123

# Baixar o arquivo quando concluido
curl http://localhost:8000/api/jobs/abc123/download-file -o video.mp4
```

---

## Dicas

- Prefira `best` quando nao souber a qualidade disponivel; o yt-dlp escolhe o melhor formato automaticamente
- Para YouTube, `1080p` e acima requer que video e audio sejam baixados separadamente e mesclados pelo ffmpeg — e normal demorar um pouco mais
- Para audios longos (podcasts, cursos), use `--quality audio` para economizar espaco
- Se o download falhar com erro de formato, tente novamente com `best` — alguns videos nao tem todas as resolucoes
- yt-dlp e atualizado frequentemente; se um site parar de funcionar, atualize: `pip install -U yt-dlp`
