# Plano de Integração: Chatterbox TTS no inemavox

**Preparado em:** 2026-02-22
**Sessão de origem:** `~/projetos/chatterbox` (Claude Code)
**Destino:** `~/projetos/inemavox/dublar_pro_v5.py`

> Este documento contém tudo que a próxima sessão Claude Code (aberta em `~/projetos/inemavox`) precisa para implementar a integração sem pesquisa adicional.

---

## Contexto: O que já foi validado

### Modelos Chatterbox disponíveis
| Modelo | Classe Python | Idiomas | Velocidade | Observação |
|--------|--------------|---------|------------|------------|
| Turbo (350M) | `chatterbox.tts_turbo.ChatterboxTurboTTS` | EN only | ~2.7s/frase | Suporta tags `[chuckle]`, `[cough]` |
| English (500M) | `chatterbox.tts.ChatterboxTTS` | EN only | ~3-5s/frase | LLaMA-based |
| Multilingual (500M) | `chatterbox.mtl_tts.ChatterboxMultilingualTTS` | 23 idiomas incl. PT/ES/FR | ~4-7s/frase | `language_id="pt"` |

### Resultados validados (RESULTADOS_VALIDACAO.md)
- Todos os 3 modelos funcionam na GB10 (128.5 GB VRAM, CUDA 13.0)
- Voice clone validado: Turbo e Multilingual (PT) com arquivo de referência
- SR de saída: **24000 Hz** (S3GEN_SR)

### Ambiente conda
- Nome: `chatterbox`
- Python: `/home/nmaldaner/miniconda3/envs/chatterbox/bin/python3`
- Deps críticas: `torch==2.10.0+cu130`, `transformers==4.46.3`, `safetensors==0.5.3`, `diffusers==0.29.0`, `numpy<1.26`, `soundfile`
- **Não** pode ser importado diretamente do venv do inemavox — deps incompatíveis

---

## Problema Arquitetural

O `dublar_pro_v5.py` roda no **venv do inemavox** (Python 3.12) ou container Docker. O Chatterbox só existe no **conda env `chatterbox`** (Python 3.11). Solução: **subprocess + JSON**.

---

## Arquivos a criar/modificar

### Arquivo 1: CRIAR `inemavox/chatterbox_tts_worker.py`

Script standalone executado pelo Python do conda env `chatterbox`. Recebe args CLI, gera WAVs, salva resultado em JSON.

```python
#!/usr/bin/env python3
"""
Worker Chatterbox TTS — executa no conda env 'chatterbox'.
Chamado por tts_chatterbox() em dublar_pro_v5.py via subprocess.

Uso:
    python3 chatterbox_tts_worker.py \
        --segments-json /path/segs.json \
        --workdir /path/workdir \
        --lang pt \
        [--ref /path/voice_sample.wav] \
        --output-json /path/result.json
"""

import argparse
import json
import sys
import time
import re
from pathlib import Path

import torch
import soundfile as sf
import numpy as np


CHATTERBOX_SR = 24000

# Idiomas suportados pelo modelo Multilingual
MTL_LANGS = {
    "pt", "pt-br", "pt_br",
    "es", "fr", "de", "it", "nl", "pl", "cs", "sk", "hu", "ro",
    "uk", "ru", "tr", "ar", "zh", "ja", "ko", "hi", "sw", "cy"
}


def get_device():
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def salvar_silencio(path, duracao_s, sr=CHATTERBOX_SR):
    """Grava silêncio para segmento que falhou."""
    n = int(duracao_s * sr)
    sf.write(str(path), np.zeros(n, dtype=np.float32), sr)


def normalizar_lang(lang: str) -> str:
    """Normaliza código de idioma para formato Chatterbox."""
    return lang.lower().replace("-", "_").split("_")[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments-json", required=True)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--lang", required=True)
    parser.add_argument("--ref", default=None, help="WAV de referência para voice clone")
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    # Carregar segmentos
    with open(args.segments_json, encoding="utf-8") as f:
        segments = json.load(f)

    workdir = Path(args.workdir)
    lang = normalizar_lang(args.lang)
    device = get_device()
    ref = args.ref if args.ref and Path(args.ref).exists() else None

    # Escolher modelo: Turbo (EN) ou Multilingual (outros)
    use_multilingual = lang != "en"

    print(f"[chatterbox_worker] device={device}, lang={lang}, modelo={'mtl' if use_multilingual else 'turbo'}", flush=True)
    if ref:
        print(f"[chatterbox_worker] voice clone: {ref}", flush=True)

    # Carregar modelo
    t0 = time.time()
    if use_multilingual:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        model = ChatterboxMultilingualTTS.from_pretrained(device=device)
    else:
        from chatterbox.tts_turbo import ChatterboxTurboTTS
        model = ChatterboxTurboTTS.from_pretrained(device=device)

    print(f"[chatterbox_worker] modelo carregado em {time.time()-t0:.1f}s", flush=True)

    seg_results = []

    for i, seg in enumerate(segments, 1):
        txt = (seg.get("text_trad") or seg.get("text") or "").strip()
        target_dur = seg.get("end", 0) - seg.get("start", 0)
        out_path = workdir / f"seg_{i:04d}.wav"

        # Texto muito curto → silêncio
        if len(re.findall(r"[A-Za-z0-9\u00C0-\u024F]", txt)) < 3:
            salvar_silencio(out_path, target_dur)
            seg_results.append({
                "idx": i, "file": str(out_path),
                "target": target_dur, "actual": target_dur, "ratio": 1.0
            })
            continue

        t0 = time.time()
        try:
            if use_multilingual:
                kwargs = {"language_id": lang}
                if ref:
                    kwargs["audio_prompt_path"] = ref
                wav = model.generate(txt, **kwargs)
            else:
                kwargs = {}
                if ref:
                    kwargs["audio_prompt_path"] = ref
                wav = model.generate(txt, **kwargs)

            audio_np = wav.squeeze().cpu().numpy()
            sf.write(str(out_path), audio_np, CHATTERBOX_SR)
            actual_dur = len(audio_np) / CHATTERBOX_SR
            ratio = actual_dur / target_dur if target_dur > 0 else 1.0

        except Exception as e:
            print(f"[chatterbox_worker] ERRO seg {i}: {e}", flush=True)
            salvar_silencio(out_path, target_dur)
            actual_dur = target_dur
            ratio = 1.0

        elapsed = time.time() - t0
        seg_results.append({
            "idx": i, "file": str(out_path),
            "target": target_dur, "actual": actual_dur, "ratio": ratio
        })

        if i % 5 == 0 or i == len(segments):
            print(f"[chatterbox_worker] progresso: {i}/{len(segments)}", flush=True)

    # Salvar resultado
    result = {"sr": CHATTERBOX_SR, "segments": seg_results}
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[chatterbox_worker] concluido: {len(seg_results)} segmentos", flush=True)


if __name__ == "__main__":
    main()
```

---

### Arquivo 2: EDITAR `inemavox/dublar_pro_v5.py`

#### Mudança A — Nova função `tts_chatterbox()` (inserir após linha 1890, antes do bloco `# ETAPA 6: TTS (EDGE - PADRAO v4)`)

```python
# ============================================================================
# ETAPA 6: TTS (CHATTERBOX - Voice Clone Neural)
# ============================================================================

def tts_chatterbox(segments, workdir, tgt_lang, voice_sample=None):
    """TTS com Chatterbox — voice clone zero-shot.

    Roteamento automático:
      - tgt_lang == 'en'  → Turbo 350M (rápido, suporta paralinguistic tags)
      - tgt_lang != 'en'  → Multilingual 500M (PT, ES, FR, DE…)

    Requer conda env 'chatterbox' em:
      /home/nmaldaner/miniconda3/envs/chatterbox/bin/python3
    Ou variável de ambiente CHATTERBOX_PYTHON apontando para o Python correto.
    """
    print("\n" + "="*60)
    print("=== ETAPA 6: TTS (Chatterbox - Voice Clone Neural) ===")
    print("="*60)

    import tempfile

    # Python do conda env chatterbox
    chatterbox_python = os.environ.get(
        "CHATTERBOX_PYTHON",
        "/home/nmaldaner/miniconda3/envs/chatterbox/bin/python3"
    )
    worker_script = Path(__file__).parent / "chatterbox_tts_worker.py"

    if not Path(chatterbox_python).exists():
        print(f"[ERRO] Python Chatterbox não encontrado: {chatterbox_python}")
        print("[DICA] Defina CHATTERBOX_PYTHON=/path/para/python3 do conda env chatterbox")
        return None, None, None

    if not worker_script.exists():
        print(f"[ERRO] Worker não encontrado: {worker_script}")
        return None, None, None

    CHATTERBOX_SR = 24000

    # Serializar segmentos
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                     delete=False, encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False)
        segs_json_path = f.name

    output_json_path = Path(workdir) / "chatterbox_result.json"

    try:
        cmd = [
            chatterbox_python, str(worker_script),
            "--segments-json", segs_json_path,
            "--workdir", str(workdir),
            "--lang", tgt_lang,
            "--output-json", str(output_json_path),
        ]
        if voice_sample and Path(voice_sample).exists():
            cmd += ["--ref", str(voice_sample)]
            print(f"[INFO] Voice clone ativo: {voice_sample}")
        else:
            print("[INFO] Sem referência de voz — usando voz padrão")

        print(f"[INFO] Iniciando Chatterbox worker (lang={tgt_lang})...")
        result = subprocess.run(
            cmd, capture_output=False, text=True, timeout=3600
        )

        if result.returncode != 0:
            print(f"[ERRO] Chatterbox worker retornou código {result.returncode}")
            return None, None, None

        # Ler resultado
        with open(output_json_path, encoding="utf-8") as f:
            data = json.load(f)

        seg_files = [Path(s["file"]) for s in data["segments"]]
        sr = data["sr"]
        metricas = [
            {"idx": s["idx"], "target": s["target"],
             "actual": s["actual"], "ratio": s["ratio"]}
            for s in data["segments"]
        ]

        ratios = [m["ratio"] for m in metricas]
        print(f"\n[STATS] TTS Chatterbox:")
        print(f"  Segmentos: {len(seg_files)}")
        print(f"  SR: {sr} Hz")
        print(f"  Ratio médio: {np.mean(ratios):.2%}")

        return seg_files, sr, metricas

    except subprocess.TimeoutExpired:
        print("[ERRO] Chatterbox worker timeout (>60min)")
        return None, None, None
    except Exception as e:
        print(f"[ERRO] tts_chatterbox falhou: {e}")
        return None, None, None
    finally:
        Path(segs_json_path).unlink(missing_ok=True)
```

#### Mudança B — Argparse (linha 2891)

Localizar:
```python
ap.add_argument("--tts", choices=["edge", "bark", "piper", "xtts"], default="edge",
```
Substituir por:
```python
ap.add_argument("--tts", choices=["edge", "bark", "piper", "xtts", "chatterbox"], default="edge",
```

#### Mudança C — Dispatch ETAPA 6 (linha 3114)

Localizar o bloco:
```python
    if args.tts == "xtts" and voice_sample:
        result = tts_xtts_clone(segs_trad, workdir, args.tgt, voice_sample)
        ...
    elif args.tts == "edge":
```

Inserir **antes** de `elif args.tts == "edge":`:
```python
    elif args.tts == "chatterbox":
        seg_files, sr_segs, tts_metrics = tts_chatterbox(
            segs_trad, workdir, args.tgt, voice_sample
        )
        if seg_files is None:
            print("[INFO] Chatterbox falhou, usando Edge como fallback...")
            seg_files, sr_segs, tts_metrics = tts_edge(
                segs_trad, workdir, args.tgt, voice=args.voice, rate=args.rate
            )
```

---

## Referência: Linhas exatas em dublar_pro_v5.py

| Local | Linha (aprox) | Ação |
|-------|--------------|------|
| Fim de `tts_xtts_clone()` | 1890 | Inserir `tts_chatterbox()` após esta linha |
| argparse `--tts` | 2891 | Adicionar `"chatterbox"` nas choices |
| Dispatch ETAPA 6 | 3114–3140 | Adicionar branch `elif args.tts == "chatterbox"` |

---

## Teste após integração

```bash
cd ~/projetos/inemavox

# Teste rápido sem clone (EN → PT com modelo multilingual)
./dublar-pro.sh --in doc/video_teste.mp4 --src en --tgt pt --tts chatterbox

# Com clone de voz (precisa de --clonar-voz para extrair voice_sample)
./dublar-pro.sh --in doc/video_teste.mp4 --src en --tgt pt --tts chatterbox --clonar-voz
```

Se quiser usar um Python diferente do conda (ex: dentro de Docker), setar:
```bash
export CHATTERBOX_PYTHON=/usr/bin/python3  # ou path do env no container
```

---

## Notas para a sessão no inemavox

1. **Não alterar** a lógica de sync/fade/mux — SR 24000 já é suportado pelo rubberband
2. **Não instalar** chatterbox no venv do inemavox — conflito certo com numpy/torch
3. O worker roda **em processo separado** — VRAM do Chatterbox não interfere com outros modelos (M2M100, Whisper) desde que não rodem em paralelo
4. Se Ollama + Chatterbox rodarem juntos, monitorar VRAM (128 GB é suficiente, mas modelo Multilingual usa ~8 GB)
5. A variável `voice_sample` já existe no pipeline (linha 3015-3017) — `--clonar-voz` a popula automaticamente
