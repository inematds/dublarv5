#!/bin/bash
# dublar-gpu.sh - inemaVOX: Executa pipeline de dublagem com GPU via Docker
# Usa container NVIDIA PyTorch otimizado para GB10 Blackwell

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="inemavox:gpu"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  inemaVOX - Pipeline via Docker (GPU)${NC}"
echo -e "${BLUE}============================================${NC}"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERRO] Docker nao encontrado${NC}"
    exit 1
fi

# Verificar NVIDIA Container Toolkit
if ! docker info 2>/dev/null | grep -q "nvidia"; then
    echo -e "${YELLOW}[AVISO] NVIDIA Container Toolkit pode nao estar configurado${NC}"
fi

# Verificar se imagem existe, senao buildar
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    echo -e "${YELLOW}[BUILD] Construindo imagem Docker (primeira vez, pode demorar)...${NC}"
    docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERRO] Falha ao construir imagem Docker${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Imagem construida com sucesso${NC}"
fi

# Verificar GPU
echo ""
echo -e "${BLUE}[HARDWARE]${NC}"
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>/dev/null | head -1)
    echo -e "  ${GREEN}GPU: $GPU_NAME${NC}"
fi
RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
echo -e "  RAM: ${RAM_GB}GB"
echo ""

# Mostrar help se sem argumentos
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Uso:${NC}"
    echo "  ./dublar-gpu.sh --in VIDEO.mp4 --src IDIOMA_ORIGEM --tgt IDIOMA_DESTINO [OPCOES]"
    echo ""
    echo -e "${YELLOW}Exemplos:${NC}"
    echo "  ./dublar-gpu.sh --in video.mp4 --src en --tgt pt"
    echo "  ./dublar-gpu.sh --in video.mp4 --src en --tgt pt --tts bark"
    echo "  ./dublar-gpu.sh --in \"https://youtube.com/watch?v=XXX\" --tgt pt --large-model"
    echo ""
    echo -e "${YELLOW}Opcoes TTS:${NC}"
    echo "  --tts edge   Microsoft Edge (online, rapido, default)"
    echo "  --tts bark   Bark TTS (offline, GPU recomendado)"
    echo "  --tts piper  Piper (offline, leve)"
    echo ""
    echo -e "${YELLOW}Opcoes de traducao:${NC}"
    echo "  --tradutor m2m100   M2M100 (offline, default)"
    echo "  --tradutor ollama   Ollama LLM (local, melhor qualidade)"
    echo "  --modelo MODEL      Modelo Ollama (ex: qwen2.5:14b, qwen2.5:72b)"
    exit 0
fi

echo -e "${GREEN}[INICIANDO] Pipeline com GPU...${NC}"
echo ""

# Executar no container Docker com GPU
docker run --rm \
    --gpus all \
    --ipc=host \
    --ulimit memlock=-1 \
    --ulimit stack=67108864 \
    --network=host \
    -v "$SCRIPT_DIR/dub_work:/app/dub_work" \
    -v "$SCRIPT_DIR/dublado:/app/dublado" \
    -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
    -e OLLAMA_HOST=http://localhost:11434 \
    "$IMAGE_NAME" "$@"

EXIT_CODE=$?
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}[CONCLUIDO] Pipeline GPU finalizado com sucesso!${NC}"
    if [ -d "$SCRIPT_DIR/dublado" ]; then
        echo -e "${GREEN}[OUTPUT] Arquivos em:${NC}"
        ls -lh "$SCRIPT_DIR/dublado/"*.mp4 2>/dev/null
    fi
else
    echo -e "${RED}[ERRO] Pipeline finalizou com codigo $EXIT_CODE${NC}"
fi
