#!/bin/bash
# instalar.sh - Script de instalação do Dublar Pro
# Instala todas as dependências necessárias

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  DUBLAR PRO - Instalação de Dependências${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Detectar sistema operacional
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    OS="other"
fi

echo -e "${BLUE}[INFO]${NC} Sistema: $OS"

# ============================================
# 1. Dependências do Sistema
# ============================================
echo ""
echo -e "${YELLOW}[1/5] Verificando dependências do sistema...${NC}"

# FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}  [OK] FFmpeg instalado${NC}"
else
    echo -e "${YELLOW}  [INSTALANDO] FFmpeg...${NC}"
    if [[ "$OS" == "linux" ]]; then
        sudo apt update && sudo apt install -y ffmpeg
    elif [[ "$OS" == "macos" ]]; then
        brew install ffmpeg
    else
        echo -e "${RED}  [ERRO] Instale FFmpeg manualmente${NC}"
        exit 1
    fi
fi

# Rubberband (opcional, para melhor time-stretch)
if command -v rubberband &> /dev/null; then
    echo -e "${GREEN}  [OK] Rubberband instalado (opcional)${NC}"
else
    echo -e "${YELLOW}  [INFO] Rubberband não instalado (opcional)${NC}"
    echo -e "${YELLOW}         Para instalar: sudo apt install rubberband-cli${NC}"
fi

# ============================================
# 2. Python
# ============================================
echo ""
echo -e "${YELLOW}[2/5] Verificando Python...${NC}"

if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}  [ERRO] Python não encontrado${NC}"
    echo -e "${YELLOW}  Instale Python 3.10+ antes de continuar${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}  [OK] Python $PYTHON_VERSION${NC}"

# Verificar versão mínima
PYTHON_MAJOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$($PYTHON_CMD -c "import sys; print(sys.version_info.minor)")

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 10 ]]; then
    echo -e "${RED}  [ERRO] Python 3.10+ necessário (encontrado: $PYTHON_VERSION)${NC}"
    exit 1
fi

# Aviso sobre Python 3.13
if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 13 ]]; then
    echo -e "${YELLOW}  [AVISO] Python 3.13+ detectado${NC}"
    echo -e "${YELLOW}          Coqui TTS não suporta esta versão${NC}"
    echo -e "${YELLOW}          Use --tts bark (padrão)${NC}"
fi

# ============================================
# 3. Pip e dependências básicas
# ============================================
echo ""
echo -e "${YELLOW}[3/5] Atualizando pip...${NC}"

$PYTHON_CMD -m pip install --upgrade pip

# ============================================
# 4. Dependências Python
# ============================================
echo ""
echo -e "${YELLOW}[4/5] Instalando dependências Python...${NC}"

# Core - NumPy e SciPy
echo -e "${BLUE}  Instalando NumPy e SciPy...${NC}"
$PYTHON_CMD -m pip install numpy scipy

# PyTorch
echo -e "${BLUE}  Instalando PyTorch...${NC}"

# Detectar GPU NVIDIA
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    echo -e "${GREEN}  [GPU] NVIDIA detectada${NC}"

    # Detectar versão CUDA
    CUDA_VERSION=$(nvidia-smi | grep -oP "CUDA Version: \K[0-9]+\.[0-9]+" || echo "")

    if [[ ! -z "$CUDA_VERSION" ]]; then
        echo -e "${GREEN}  [GPU] CUDA $CUDA_VERSION${NC}"

        # Instalar PyTorch com CUDA
        CUDA_MAJOR=$(echo $CUDA_VERSION | cut -d'.' -f1)

        if [[ $CUDA_MAJOR -ge 12 ]]; then
            echo -e "${BLUE}  Instalando PyTorch com CUDA 12.x...${NC}"
            $PYTHON_CMD -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        elif [[ $CUDA_MAJOR -ge 11 ]]; then
            echo -e "${BLUE}  Instalando PyTorch com CUDA 11.8...${NC}"
            $PYTHON_CMD -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
        else
            echo -e "${YELLOW}  [AVISO] CUDA $CUDA_VERSION pode não ser suportado${NC}"
            $PYTHON_CMD -m pip install torch torchvision torchaudio
        fi
    else
        # Instalar PyTorch padrão
        $PYTHON_CMD -m pip install torch torchvision torchaudio
    fi
else
    echo -e "${YELLOW}  [CPU] GPU NVIDIA não detectada - instalando versão CPU${NC}"
    $PYTHON_CMD -m pip install torch torchvision torchaudio
fi

# Transformers e Whisper
echo -e "${BLUE}  Instalando Transformers e Whisper...${NC}"
$PYTHON_CMD -m pip install transformers faster-whisper

# Dependências de tradução
echo -e "${BLUE}  Instalando dependências de tradução...${NC}"
$PYTHON_CMD -m pip install sentencepiece protobuf sacremoses

# TTS - Bark
echo -e "${BLUE}  Instalando Bark (TTS)...${NC}"
$PYTHON_CMD -m pip install bark

# Coqui TTS (apenas Python < 3.13)
if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 13 ]]; then
    echo -e "${BLUE}  Instalando Coqui TTS...${NC}"
    $PYTHON_CMD -m pip install TTS || echo -e "${YELLOW}  [AVISO] Coqui TTS falhou - use Bark${NC}"
fi

# Processamento de áudio
echo -e "${BLUE}  Instalando bibliotecas de áudio...${NC}"
$PYTHON_CMD -m pip install librosa soundfile Pillow

# ============================================
# 5. Verificação final
# ============================================
echo ""
echo -e "${YELLOW}[5/5] Verificando instalação...${NC}"

# Testar imports
$PYTHON_CMD << 'EOF'
import sys

modules = [
    ("numpy", "NumPy"),
    ("scipy", "SciPy"),
    ("torch", "PyTorch"),
    ("transformers", "Transformers"),
    ("faster_whisper", "Faster-Whisper"),
    ("bark", "Bark TTS"),
    ("librosa", "Librosa"),
    ("soundfile", "SoundFile"),
]

print("")
all_ok = True

for module, name in modules:
    try:
        __import__(module)
        print(f"  \033[92m[OK]\033[0m {name}")
    except ImportError:
        print(f"  \033[91m[ERRO]\033[0m {name}")
        all_ok = False

# Verificar GPU
print("")
import torch
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    print(f"  \033[92m[GPU]\033[0m {gpu_name}")
else:
    print(f"  \033[93m[CPU]\033[0m GPU não disponível")

if all_ok:
    print("")
    print("\033[92m============================================\033[0m")
    print("\033[92m  INSTALAÇÃO CONCLUÍDA COM SUCESSO!\033[0m")
    print("\033[92m============================================\033[0m")
    print("")
    print("  Para usar:")
    print("    ./dublar-pro.sh --in video.mp4 --src en --tgt pt")
    print("")
else:
    print("")
    print("\033[91m[ERRO] Algumas dependências falharam\033[0m")
    sys.exit(1)
EOF

echo ""
