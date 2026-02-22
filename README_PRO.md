# inemaVOX - Dublar Pro v3.0 (legado)

Pipeline de voz profissional com todas as otimizações de qualidade.

## Melhorias Implementadas

### 1. Qualidade da Tradução

| Melhoria | Descrição |
|----------|-----------|
| **Dicionário de correções** | Corrige automaticamente erros comuns ("escândalo" → "zero") |
| **Proteção de termos técnicos** | Preserva palavras como "API", "callback", "prompt" |
| **Glossário técnico** | 100+ termos técnicos mapeados corretamente |
| **Modelo M2M100 grande** | Opção `--large-model` para usar 1.2B (melhor qualidade) |
| **Simplificação automática** | Se tradução muito longa, simplifica antes do TTS |

### 2. Qualidade do TTS

| Melhoria | Descrição |
|----------|-----------|
| **Temperaturas otimizadas** | `text_temp=0.7, wave_temp=0.5` (fala mais natural e rápida) |
| **Multi-pass retry** | Se áudio muito longo, tenta até 3x com temperaturas menores |
| **Estimativa pré-TTS** | Calcula duração esperada ANTES de gerar |
| **Vozes otimizadas** | Default: `v2/pt_speaker_3` (mais natural) |

### 3. Sincronização

| Melhoria | Descrição |
|----------|-----------|
| **Tolerância ajustada** | Default: 10% (mais flexível) |
| **Rubberband** | Time-stretch com preservação de pitch (opcional) |
| **Smart sync melhorado** | Lógica mais inteligente de PAD vs FIT |

### 4. Outras Melhorias

- **Checkpoint system**: Salva progresso, pode continuar se interromper
- **Métricas de qualidade**: Gera relatório de sincronização
- **Logs detalhados**: JSON com todas as configurações
- **Detecção automática**: GPU/CPU sem configuração manual

---

## Uso Básico

```bash
# Dublagem simples
./dublar-pro.sh --in video.mp4 --src en --tgt pt

# Com Coqui TTS (mais rápido)
./dublar-pro.sh --in video.mp4 --src en --tgt pt --tts coqui

# Com modelo grande (melhor tradução, requer +4GB VRAM)
./dublar-pro.sh --in video.mp4 --src en --tgt pt --large-model

# Máxima qualidade
./dublar-pro.sh --in video.mp4 --src en --tgt pt --large-model --use-rubberband
```

---

## Opções Completas

```
OBRIGATÓRIOS:
  --in VIDEO          Vídeo de entrada
  --src LANG          Idioma de origem (en, es, fr, de, ja, zh, etc)
  --tgt LANG          Idioma de destino (pt, en, es, etc)

SAÍDA:
  --out VIDEO         Vídeo de saída (default: video_dublado.mp4)
  --outdir DIR        Diretório de saída (default: dublado/)

TTS:
  --tts ENGINE        bark ou coqui (default: bark)
  --voice VOZ         Voz do TTS (default: v2/pt_speaker_3)
  --texttemp FLOAT    Temperatura de texto Bark (default: 0.7)
  --wavetemp FLOAT    Temperatura de waveform Bark (default: 0.5)
  --max-retries N     Tentativas TTS se muito longo (default: 2)

TRADUÇÃO:
  --large-model       Usar M2M100 1.2B (melhor qualidade)
  --whisper-model     tiny, small, medium, large (default: medium)

SINCRONIZAÇÃO:
  --sync MODE         none, fit, pad, smart (default: smart)
  --tolerance FLOAT   Tolerância (default: 0.1 = 10%)
  --maxstretch FLOAT  Max compressão (default: 1.4 = 40%)
  --use-rubberband    Usar rubberband para time-stretch

OUTROS:
  --maxdur FLOAT      Duração máxima de segmento (default: 10s)
  --rate INT          Sample rate final (default: 24000)
  --bitrate STR       Bitrate AAC (default: 192k)
  --fade 0|1          Aplicar fade (default: 1)
```

---

## Vozes Disponíveis (Bark)

| Voz | Descrição |
|-----|-----------|
| `v2/pt_speaker_1` | Masculina 1 |
| `v2/pt_speaker_2` | Masculina 2 |
| `v2/pt_speaker_3` | Masculina 3 (recomendada) |
| `v2/pt_speaker_4` | Feminina 1 |
| `v2/pt_speaker_5` | Feminina 2 |

---

## Requisitos de Hardware

### Mínimo (CPU)
- 8GB RAM
- 10GB disco (modelos)
- Tempo: ~30min para 5min de vídeo

### Recomendado (GPU)
- 6GB+ VRAM (GTX 1060 ou superior)
- 16GB RAM
- Tempo: ~10min para 5min de vídeo

### Para `--large-model`
- 8GB+ VRAM
- 16GB+ RAM

---

## Arquivos Gerados

```
dub_work/
├── audio_src.wav           # Áudio extraído
├── asr.json, asr.srt       # Transcrição original
├── asr_trad.json, .srt     # Tradução
├── seg_0001.wav ...        # Segmentos TTS
├── dub_raw.wav             # Concatenado
├── dub_final.wav           # Pós-processado
├── logs.json               # Configurações
├── quality_metrics.json    # Métricas
└── checkpoint.json         # Checkpoint

dublado/
└── video_dublado.mp4       # Resultado final
```

---

## Correções Automáticas de Tradução

O sistema corrige automaticamente:

| Erro Comum | Correção |
|------------|----------|
| "escândalo" | "zero" (from scratch) |
| "promptes" | "prompts" |
| "povos" | "pessoas" |
| "nossos povos" | "nossa equipe" |
| Falta espaço após ponto | Adiciona espaço |

---

## Termos Preservados

Não são traduzidos:
- Programação: `string`, `array`, `function`, `callback`, `async`, `await`
- Ferramentas: `git`, `docker`, `npm`, `webpack`
- Protocolos: `API`, `REST`, `HTTP`, `JSON`, `HTML`, `CSS`
- Produtos: `Claude Code`, `ChatGPT`, `GitHub`

---

## Troubleshooting

### Áudio muito lento
```bash
# Usar temperaturas menores
--texttemp 0.6 --wavetemp 0.4

# Ou usar Coqui (mais rápido)
--tts coqui
```

### Tradução com erros
```bash
# Usar modelo maior
--large-model
```

### Sem GPU
```bash
# O sistema detecta automaticamente e usa CPU
# Para forçar CPU:
export CUDA_VISIBLE_DEVICES=""
./dublar-pro.sh ...
```

### Falta de memória
```bash
# Usar modelo Whisper menor
--whisper-model small

# Não usar modelo grande de tradução
# (não passar --large-model)
```

---

## Comparação: dublar.py vs dublar_pro.py

| Feature | dublar.py | dublar_pro.py |
|---------|-----------|---------------|
| Correção de tradução | Não | Sim |
| Proteção termos técnicos | Não | Sim |
| Estimativa pré-TTS | Não | Sim |
| Multi-pass TTS | Não | Sim |
| Rubberband | Não | Sim |
| Métricas qualidade | Não | Sim |
| Checkpoint/resume | Não | Sim |
| Temperaturas otimizadas | 0.6/0.6 | 0.7/0.5 |
| Tolerância default | 5% | 10% |
