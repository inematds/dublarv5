# Instalação do inemaVOX em Servidor Linux

Este guia mostra como instalar e configurar o inemaVOX em um servidor Linux.

## ⚡ TL;DR - Início Rápido

```bash
git clone https://github.com/inematds/dublar.git
cd dublar
python3 -m venv venv
source venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python3 dublar.py video.mp4 --src_lang en --tgt_lang pt --tts bark --sync smart
```

**Os diretórios `dub_work/` e `dublado/` são criados AUTOMATICAMENTE - você não precisa criar nada!**

---

## 1. Clonar o Repositório

```bash
# Clone o repositório
git clone https://github.com/inematds/dublar.git
cd dublar
```

## 2. Instalar Dependências do Sistema

### Ubuntu/Debian:
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.10 ou superior
sudo apt install -y python3 python3-pip python3-venv

# Instalar FFmpeg (essencial para processamento de vídeo)
sudo apt install -y ffmpeg

# Instalar dependências de áudio
sudo apt install -y libsndfile1 libsndfile1-dev

# Verificar instalação
python3 --version  # Deve ser 3.10+
ffmpeg -version
ffprobe -version
```

### CentOS/RHEL/Rocky Linux:
```bash
# Habilitar EPEL repository
sudo yum install -y epel-release

# Instalar Python e FFmpeg
sudo yum install -y python3 python3-pip python3-devel
sudo yum install -y ffmpeg ffmpeg-devel

# Instalar dependências de áudio
sudo yum install -y libsndfile libsndfile-devel
```

## 3. Criar Ambiente Virtual Python

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate

# Atualizar pip
pip install --upgrade pip wheel setuptools
```

## 4. Instalar Dependências Python

### Opção A: CPU Only (Mais simples, funciona em qualquer servidor)
```bash
# Instalar PyTorch para CPU
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Instalar demais dependências
pip install -r requirements.txt
```

### Opção B: GPU (Se tiver NVIDIA GPU)
```bash
# Verificar se tem GPU NVIDIA
nvidia-smi

# Instalar PyTorch com CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Instalar demais dependências
pip install -r requirements.txt

# Testar GPU
python3 test_gpu.py
```

## 5. Usar o Sistema

### Ativar ambiente sempre que usar:
```bash
cd dublar
source venv/bin/activate
```

### Executar dublagem (equivalente ao dublar.bat no Windows):
```bash
# Sintaxe básica
python3 dublar.py video.mp4 --src_lang en --tgt_lang pt --tts bark --sync smart

# Exemplo completo
python3 dublar.py meu_video.mp4 \
    --src_lang en \
    --tgt_lang pt \
    --tts bark \
    --sync smart \
    --voice pt_speaker_5

# Ajuda completa
python3 dublar.py --help
```

### Parâmetros principais:
- `--src_lang`: Idioma de origem (en, es, fr, etc.)
- `--tgt_lang`: Idioma de destino (pt, en, es, etc.)
- `--tts`: Engine de voz (bark, coqui)
- `--sync`: Modo de sincronização (none, fit, pad, smart)
- `--voice`: Voz específica a usar

## 6. Scripts Auxiliares

### Criar script para facilitar uso (opcional):
```bash
# Criar arquivo dublar.sh
cat > dublar.sh << 'EOF'
#!/bin/bash
# Script para executar dublar no Linux
source venv/bin/activate
python3 dublar.py "$@"
EOF

# Dar permissão de execução
chmod +x dublar.sh

# Usar assim:
./dublar.sh video.mp4 --src_lang en --tgt_lang pt --tts bark --sync smart
```

## 7. Testar Instalação

```bash
# Ativar ambiente
source venv/bin/activate

# Testar GPU (se aplicável)
python3 test_gpu.py

# Testar Whisper
python3 test_whisper_gpu.py

# Teste rápido completo
python3 test_quick.py
```

## 8. Troubleshooting

### FFmpeg não encontrado:
```bash
# Verificar se está no PATH
which ffmpeg
which ffprobe

# Se não estiver, adicionar ao PATH
export PATH=$PATH:/usr/local/bin
```

### Erro de permissão:
```bash
# Dar permissão aos scripts Python
chmod +x dublar.py dublar2.py dublar3.py
```

### Erro de memória/GPU:
```bash
# Usar CPU em vez de GPU
# Editar dublar.py e forçar device="cpu"
# Ou usar menos threads:
export OMP_NUM_THREADS=4
```

### Dependências faltando:
```bash
# Reinstalar tudo
pip install --upgrade --force-reinstall -r requirements.txt
```

## 9. Manter Atualizado

```bash
# Puxar atualizações
git pull origin main

# Atualizar dependências se necessário
pip install --upgrade -r requirements.txt
```

## 10. Desativar Ambiente

```bash
# Quando terminar de usar
deactivate
```

## Estrutura de Diretórios

### O que você precisa criar:
```
dublar/
├── venv/              # ✋ VOCÊ CRIA: python3 -m venv venv
```

### O que vem do GitHub (clone):
```
dublar/
├── dublar.py          # Scripts Python
├── dublar2.py
├── dublar3.py
├── dublar31.py
├── requirements.txt   # Dependências
├── test_*.py          # Scripts de teste
├── *.md              # Documentação
├── *.bat              # Scripts Windows (ignore no Linux)
└── .gitignore
```

### O que é criado AUTOMATICAMENTE ao rodar:
```
dublar/
├── dub_work/          # ✅ AUTO: Arquivos temporários de processamento
│   ├── audio_src.wav      # Áudio extraído do vídeo
│   ├── asr.srt            # Transcrição original
│   ├── asr_trad.srt       # Tradução
│   ├── seg_*.wav          # Segmentos de áudio
│   ├── dub_raw.wav        # Áudio dublado antes do pós-processamento
│   ├── dub_final.wav      # Áudio dublado final
│   └── logs.json          # Log completo do processo
│
└── dublado/           # ✅ AUTO: Vídeos dublados finalizados (saída)
    └── video_dublado.mp4  # Seu vídeo dublado final
```

### Resumo:
- **VOCÊ CRIA**: Apenas `venv/` com `python3 -m venv venv`
- **GIT CLONE**: Todo o código-fonte e documentação
- **AUTOMÁTICO**: `dub_work/` e `dublado/` são criados quando você roda o script pela primeira vez

## Notas Importantes

1. **Diretórios são criados automaticamente** - Não crie `dub_work/` ou `dublado/` manualmente!
2. **Sempre ative o ambiente virtual** antes de usar: `source venv/bin/activate`
3. **FFmpeg é obrigatório** - sem ele nada funciona
4. **GPU é opcional** - funciona perfeitamente em CPU (apenas mais lento)
5. **Scripts .bat não funcionam** no Linux - use os comandos Python diretamente
6. **Mínimo 8GB RAM** recomendado (16GB+ para vídeos longos)

## Requisitos de Sistema

- **OS**: Linux (Ubuntu 20.04+, CentOS 8+, Debian 11+)
- **Python**: 3.10 ou superior
- **RAM**: 8GB mínimo, 16GB+ recomendado
- **Disco**: 10GB+ para modelos AI
- **GPU** (opcional): NVIDIA com CUDA 11.8+
- **FFmpeg**: Versão recente com libx264

## Suporte

Para problemas, consulte:
- README.md - Documentação geral
- MAPA_ARQUIVOS.md - Estrutura do projeto
- test_quick.py - Testes rápidos
