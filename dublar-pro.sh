#!/bin/bash
# dublar-pro.sh - inemaVOX: Script de execução do pipeline
# Detecta automaticamente GPU/CPU e configura ambiente

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  inemaVOX - Pipeline de Dublagem${NC}"
echo -e "${BLUE}============================================${NC}"

# Verificar Python
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERRO] Python não encontrado${NC}"
    exit 1
fi

# Usar python ou python3
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

echo -e "${GREEN}[OK] Python: $($PYTHON_CMD --version)${NC}"

# Verificar FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}[ERRO] FFmpeg não encontrado${NC}"
    echo -e "${YELLOW}Instale com: sudo apt install ffmpeg${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] FFmpeg instalado${NC}"

# Detectar GPU
echo ""
echo -e "${BLUE}[HARDWARE]${NC}"

GPU_AVAILABLE=0
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi &> /dev/null; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>/dev/null | head -1)
        GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
        echo -e "  ${GREEN}GPU: $GPU_NAME (${GPU_MEM}MB VRAM)${NC}"
        GPU_AVAILABLE=1
    fi
fi

if [ $GPU_AVAILABLE -eq 0 ]; then
    echo -e "  ${YELLOW}GPU: Não detectada (usando CPU)${NC}"
fi

# Verificar RAM
RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
echo -e "  RAM: ${RAM_GB}GB"

# Verificar rubberband (opcional)
if command -v rubberband &> /dev/null; then
    echo -e "  ${GREEN}Rubberband: Disponível${NC}"
else
    echo -e "  ${YELLOW}Rubberband: Não instalado (opcional)${NC}"
fi

echo ""

# Verificar argumentos
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Uso:${NC}"
    echo "  ./dublar-pro.sh --in VIDEO.mp4 --src IDIOMA_ORIGEM --tgt IDIOMA_DESTINO [OPCOES]"
    echo ""
    echo -e "${YELLOW}Exemplos:${NC}"
    echo "  ./dublar-pro.sh --in video.mp4 --src en --tgt pt"
    echo "  ./dublar-pro.sh --in video.mp4 --src en --tgt pt --tts coqui"
    echo "  ./dublar-pro.sh --in video.mp4 --src en --tgt pt --large-model"
    echo ""
    echo -e "${YELLOW}Opções principais:${NC}"
    echo "  --in VIDEO          Vídeo de entrada"
    echo "  --src LANG          Idioma de origem (en, es, fr, de, etc)"
    echo "  --tgt LANG          Idioma de destino (pt, en, es, etc)"
    echo "  --out VIDEO         Vídeo de saída (opcional)"
    echo "  --tts ENGINE        bark ou coqui (default: bark)"
    echo "  --voice VOZ         Voz do TTS (default: v2/pt_speaker_3)"
    echo "  --large-model       Usar modelo M2M100 maior (melhor qualidade)"
    echo "  --sync MODE         none, fit, pad, smart (default: smart)"
    echo "  --tolerance FLOAT   Tolerância de sync (default: 0.1)"
    echo "  --use-rubberband    Usar rubberband para time-stretch"
    echo ""
    echo -e "${YELLOW}Para ajuda completa:${NC}"
    echo "  $PYTHON_CMD dublar_pro.py --help"
    exit 0
fi

# Executar
echo -e "${GREEN}[INICIANDO]${NC}"
echo ""
$PYTHON_CMD dublar_pro.py "$@"

echo ""
echo -e "${GREEN}[CONCLUÍDO]${NC}"
