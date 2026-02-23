# dublar_pro.py
# Pipeline de dublagem PROFISSIONAL com todas as otimizações
# Inclui: tradução melhorada, TTS otimizado, sincronização avançada, paralelização

import os, sys, json, csv, argparse, subprocess, shutil, re, warnings
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
import numpy as np

warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================

VERSION = "3.0.0"

# Caracteres por segundo por idioma (para estimativa de duração)
CPS_POR_IDIOMA = {
    "pt": 14, "pt-br": 14, "pt_br": 14,
    "en": 12, "en-us": 12, "en-gb": 12,
    "es": 13, "es-es": 13, "es-mx": 13,
    "fr": 13, "de": 12, "it": 13,
    "ja": 8, "zh": 6, "ko": 9,
    "ru": 12, "ar": 11, "hi": 12,
}

# ============================================================================
# DICIONÁRIO DE CORREÇÕES DE TRADUÇÃO
# ============================================================================

CORRECOES_TRADUCAO = {
    # Erros comuns de tradução literal
    "escândalo": "zero",                    # "from scratch" mal traduzido
    "a partir de escândalo": "do zero",
    "desde escândalo": "do zero",
    "promptes": "prompts",
    "prompts": "prompts",                   # manter em inglês
    "povos": "pessoas",
    "nossos povos": "nossa equipe",
    "colocam juntos": "criaram",
    "colocaram juntos": "criaram",
    "pôr junto": "criar",

    # Expressões idiomáticas
    "fora da caixa": "inovador",
    "na mesma página": "alinhados",
    "bola na trave": "quase conseguiu",
    "dar uma olhada": "verificar",
    "no final do dia": "no fim das contas",
    "tocar base": "entrar em contato",

    # Termos técnicos que devem ficar em inglês
    "cadeia de caracteres": "string",
    "matriz": "array",
    "retorno de chamada": "callback",
    "ponto final": "endpoint",
    "gancho": "hook",
    "estado": "state",
    "propriedades": "props",
    "renderizar": "renderizar",

    # Correções de pontuação
    ".Então": ". Então",
    ".Vou": ". Vou",
    ".Bem": ". Bem",
    ".Isso": ". Isso",
    ".E": ". E",
    ".O": ". O",
    ".A": ". A",
    "!Então": "! Então",
    "?Então": "? Então",

    # Nomes de produtos (preservar)
    "Código Claude": "Claude Code",
    "Código Nuvem": "Cloud Code",

    # ============================================
    # NOVAS CORREÇÕES - Inglês não traduzido
    # ============================================

    # let's / let me - muito comum não traduzir
    "let's": "vamos",
    "Let's": "Vamos",
    "let me": "deixe-me",
    "Let me": "Deixe-me",
    "let us": "vamos",
    "Let us": "Vamos",

    # Contrações em inglês que escapam
    "I'm": "eu estou",
    "I'll": "eu vou",
    "I've": "eu tenho",
    "we're": "nós estamos",
    "we'll": "nós vamos",
    "we've": "nós temos",
    "you're": "você está",
    "you'll": "você vai",
    "you've": "você tem",
    "it's": "é",
    "that's": "isso é",
    "there's": "há",
    "here's": "aqui está",
    "what's": "o que é",
    "don't": "não",
    "doesn't": "não",
    "didn't": "não",
    "can't": "não pode",
    "won't": "não vai",
    "wouldn't": "não iria",
    "couldn't": "não poderia",
    "shouldn't": "não deveria",
    "isn't": "não é",
    "aren't": "não são",
    "wasn't": "não estava",
    "weren't": "não estavam",
    "haven't": "não tenho",
    "hasn't": "não tem",
    "hadn't": "não tinha",

    # Palavras comuns que escapam
    "the": "o",
    "and": "e",
    "but": "mas",
    "or": "ou",
    "so": "então",
    "just": "apenas",
    "like": "como",
    "really": "realmente",
    "actually": "na verdade",
    "basically": "basicamente",
    "obviously": "obviamente",
    "probably": "provavelmente",
    "definitely": "definitivamente",
    "exactly": "exatamente",

    # Verbos comuns
    "go": "ir",
    "going": "indo",
    "gonna": "vou",
    "want": "quero",
    "need": "preciso",
    "know": "sei",
    "think": "acho",
    "see": "ver",
    "look": "olhar",
    "make": "fazer",
    "take": "pegar",
    "get": "obter",
    "give": "dar",
    "use": "usar",
    "try": "tentar",
    "come": "vir",
    "work": "trabalhar",
    "call": "chamar",
    "show": "mostrar",

    # Frases comuns em inglês
    "you know": "sabe",
    "I mean": "quero dizer",
    "kind of": "tipo",
    "sort of": "meio que",
    "a lot of": "muito",
    "a little bit": "um pouco",
    "right now": "agora mesmo",
    "of course": "claro",
    "by the way": "a propósito",
    "as well": "também",
    "at least": "pelo menos",
    "at all": "de forma alguma",
    "in fact": "na verdade",
    "for example": "por exemplo",

    # Correções de zoom/let que vimos
    "zoom de let": "vamos dar zoom",
    "zoom de lets": "vamos dar zoom",
    "zoom de let's": "vamos dar zoom",

    # Mais palavras comuns que escapam
    "this": "isso",
    "that": "isso",
    "these": "esses",
    "those": "aqueles",
    "here": "aqui",
    "there": "lá",
    "where": "onde",
    "when": "quando",
    "what": "o que",
    "which": "qual",
    "who": "quem",
    "how": "como",
    "why": "por que",

    # Mais verbos
    "explain": "explicar",
    "build": "construir",
    "create": "criar",
    "write": "escrever",
    "read": "ler",
    "run": "executar",
    "start": "iniciar",
    "stop": "parar",
    "open": "abrir",
    "close": "fechar",
    "save": "salvar",
    "load": "carregar",
    "send": "enviar",
    "receive": "receber",
    "copy": "copiar",
    "paste": "colar",
    "cut": "cortar",
    "delete": "deletar",
    "add": "adicionar",
    "remove": "remover",
    "change": "mudar",
    "update": "atualizar",
    "check": "verificar",
    "test": "testar",
    "fix": "corrigir",
    "help": "ajudar",
    "find": "encontrar",
    "search": "buscar",
    "click": "clicar",
    "select": "selecionar",
    "choose": "escolher",
    "pick": "pegar",
    "set": "definir",
    "put": "colocar",

    # Pronomes e artigos
    "you": "você",
    "your": "seu",
    "my": "meu",
    "our": "nosso",
    "their": "deles",
    "his": "dele",
    "her": "dela",
    "its": "seu",
    "some": "algum",
    "any": "qualquer",
    "all": "todo",
    "each": "cada",
    "every": "todo",
    "many": "muitos",
    "much": "muito",
    "more": "mais",
    "most": "maioria",
    "other": "outro",
    "another": "outro",
    "same": "mesmo",
    "different": "diferente",
    "new": "novo",
    "old": "antigo",
    "good": "bom",
    "bad": "ruim",
    "great": "ótimo",
    "big": "grande",
    "small": "pequeno",
    "first": "primeiro",
    "last": "último",
    "next": "próximo",
    "only": "apenas",
    "very": "muito",
    "even": "mesmo",
    "still": "ainda",
    "already": "já",
    "now": "agora",
    "then": "então",
    "here": "aqui",
    "again": "novamente",
    "always": "sempre",
    "never": "nunca",
    "often": "frequentemente",
    "sometimes": "às vezes",
    "maybe": "talvez",
    "yes": "sim",
    "no": "não",
    "ok": "ok",
    "okay": "ok",
    "please": "por favor",
    "thanks": "obrigado",
    "sorry": "desculpe",
    "sure": "claro",
    "right": "certo",
    "wrong": "errado",
    "true": "verdadeiro",
    "false": "falso",

    # Conectivos
    "because": "porque",
    "since": "desde",
    "while": "enquanto",
    "if": "se",
    "unless": "a menos que",
    "until": "até",
    "after": "depois",
    "before": "antes",
    "during": "durante",
    "through": "através",
    "into": "para dentro",
    "onto": "para cima",
    "with": "com",
    "without": "sem",
    "about": "sobre",
    "around": "ao redor",
    "between": "entre",
    "among": "entre",
    "under": "sob",
    "over": "sobre",
    "above": "acima",
    "below": "abaixo",
    "from": "de",
    "to": "para",
    "for": "para",
    "by": "por",
    "at": "em",
    "in": "em",
    "on": "em",
    "off": "fora",
    "up": "cima",
    "down": "baixo",
    "out": "fora",
    "back": "voltar",
    "away": "longe",
    "together": "juntos",
    "apart": "separados",

    # Palavras que ainda escapam
    "something": "algo",
    "nothing": "nada",
    "everything": "tudo",
    "anything": "qualquer coisa",
    "someone": "alguém",
    "nobody": "ninguém",
    "everyone": "todos",
    "anyone": "qualquer um",
    "somewhere": "algum lugar",
    "nowhere": "nenhum lugar",
    "everywhere": "em todo lugar",
    "anywhere": "em qualquer lugar",
    "thing": "coisa",
    "things": "coisas",
    "time": "tempo",
    "times": "vezes",
    "way": "forma",
    "ways": "formas",
    "place": "lugar",
    "places": "lugares",
    "part": "parte",
    "parts": "partes",
    "point": "ponto",
    "points": "pontos",
    "example": "exemplo",
    "examples": "exemplos",
    "question": "pergunta",
    "questions": "perguntas",
    "answer": "resposta",
    "answers": "respostas",
    "problem": "problema",
    "problems": "problemas",
    "solution": "solução",
    "solutions": "soluções",
    "result": "resultado",
    "results": "resultados",
    "idea": "ideia",
    "ideas": "ideias",
    "reason": "razão",
    "reasons": "razões",
    "fact": "fato",
    "facts": "fatos",
    "kind": "tipo",
    "type": "tipo",
    "types": "tipos",
    "sort": "tipo",
    "lot": "muito",
    "lots": "muitos",
    "bit": "pouco",
    "piece": "pedaço",
    "pieces": "pedaços",
    "number": "número",
    "numbers": "números",
    "word": "palavra",
    "words": "palavras",
    "name": "nome",
    "names": "nomes",
    "day": "dia",
    "days": "dias",
    "week": "semana",
    "weeks": "semanas",
    "month": "mês",
    "months": "meses",
    "year": "ano",
    "years": "anos",
    "today": "hoje",
    "tomorrow": "amanhã",
    "yesterday": "ontem",
    "morning": "manhã",
    "afternoon": "tarde",
    "evening": "noite",
    "night": "noite",
    "hour": "hora",
    "hours": "horas",
    "minute": "minuto",
    "minutes": "minutos",
    "second": "segundo",
    "seconds": "segundos",

    # Verbos no gerúndio/particípio
    "doing": "fazendo",
    "making": "fazendo",
    "getting": "obtendo",
    "taking": "pegando",
    "giving": "dando",
    "using": "usando",
    "trying": "tentando",
    "coming": "vindo",
    "working": "trabalhando",
    "looking": "olhando",
    "thinking": "pensando",
    "knowing": "sabendo",
    "seeing": "vendo",
    "showing": "mostrando",
    "building": "construindo",
    "creating": "criando",
    "writing": "escrevendo",
    "reading": "lendo",
    "running": "executando",
    "starting": "iniciando",
    "stopping": "parando",
    "opening": "abrindo",
    "closing": "fechando",
    "saving": "salvando",
    "loading": "carregando",
    "sending": "enviando",
    "adding": "adicionando",
    "removing": "removendo",
    "changing": "mudando",
    "updating": "atualizando",
    "checking": "verificando",
    "testing": "testando",
    "fixing": "corrigindo",
    "helping": "ajudando",
    "finding": "encontrando",
    "searching": "buscando",
    "clicking": "clicando",
    "selecting": "selecionando",
    "choosing": "escolhendo",
    "setting": "definindo",
    "putting": "colocando",
    "calling": "chamando",

    # do/does/did
    "do": "fazer",
    "does": "faz",
    "did": "fez",
    "done": "feito",
}

# Termos que NUNCA devem ser traduzidos
TERMOS_PRESERVAR = {
    # Programação
    "string", "array", "boolean", "null", "undefined", "true", "false",
    "const", "let", "var", "function", "class", "return", "async", "await",
    "promise", "callback", "middleware", "endpoint", "props", "state", "hook",
    "import", "export", "default", "extends", "interface", "type",

    # Ferramentas
    "git", "commit", "push", "pull", "merge", "branch", "checkout",
    "npm", "yarn", "pip", "docker", "kubernetes", "webpack", "babel",

    # Protocolos e formatos
    "API", "REST", "HTTP", "HTTPS", "JSON", "XML", "HTML", "CSS",
    "localhost", "URL", "URI", "DNS", "SSH", "FTP",

    # Linguagens e frameworks
    "Python", "JavaScript", "TypeScript", "React", "Node", "Vue", "Angular",
    "Django", "Flask", "FastAPI", "Express", "Next.js", "Nuxt",

    # Produtos
    "Claude Code", "ChatGPT", "GPT", "OpenAI", "Anthropic",
    "GitHub", "GitLab", "Bitbucket", "AWS", "Azure", "Google Cloud",

    # IA/ML
    "prompt", "prompts", "token", "tokens", "embedding", "embeddings",
    "transformer", "attention", "encoder", "decoder", "fine-tuning",
    "LLM", "GPT", "BERT", "model", "weights", "inference",
}

# ============================================================================
# GLOSSÁRIO TÉCNICO EXPANDIDO
# ============================================================================

GLOSSARIO_TECNICO = {
    # Programação básica
    "variable": "variável",
    "parameter": "parâmetro",
    "argument": "argumento",
    "method": "método",
    "property": "propriedade",
    "attribute": "atributo",
    "instance": "instância",
    "constructor": "construtor",
    "destructor": "destrutor",
    "inheritance": "herança",
    "polymorphism": "polimorfismo",
    "encapsulation": "encapsulamento",
    "abstraction": "abstração",

    # Web development
    "request": "requisição",
    "response": "resposta",
    "header": "cabeçalho",
    "body": "corpo",
    "query": "consulta",
    "route": "rota",
    "controller": "controlador",
    "view": "visualização",
    "template": "template",
    "component": "componente",
    "directive": "diretiva",
    "service": "serviço",
    "provider": "provedor",
    "dependency injection": "injeção de dependência",

    # Database
    "database": "banco de dados",
    "table": "tabela",
    "column": "coluna",
    "row": "linha",
    "record": "registro",
    "field": "campo",
    "primary key": "chave primária",
    "foreign key": "chave estrangeira",
    "index": "índice",
    "transaction": "transação",
    "rollback": "rollback",

    # DevOps
    "deployment": "deploy",
    "container": "container",
    "image": "imagem",
    "volume": "volume",
    "network": "rede",
    "orchestration": "orquestração",
    "scaling": "escalabilidade",
    "load balancer": "balanceador de carga",
    "reverse proxy": "proxy reverso",
    "CI/CD": "CI/CD",
    "pipeline": "pipeline",

    # Testing
    "unit test": "teste unitário",
    "integration test": "teste de integração",
    "end-to-end test": "teste end-to-end",
    "mock": "mock",
    "stub": "stub",
    "assertion": "asserção",
    "coverage": "cobertura",
    "regression": "regressão",

    # Agile
    "sprint": "sprint",
    "backlog": "backlog",
    "user story": "user story",
    "epic": "epic",
    "task": "tarefa",
    "bug": "bug",
    "feature": "feature",
    "release": "release",
    "milestone": "milestone",
}

# ============================================================================
# UTILITÁRIOS BÁSICOS
# ============================================================================

def sh(cmd, cwd=None, capture=False, timeout=300):
    """Executa comando shell com tratamento de erro melhorado"""
    cmd_str = " ".join(map(str, cmd))
    print(f">> {cmd_str[:100]}{'...' if len(cmd_str) > 100 else ''}")

    try:
        if capture:
            result = subprocess.run(cmd, check=True, cwd=cwd,
                                   capture_output=True, text=True, timeout=timeout)
            return result.stdout
        else:
            subprocess.run(cmd, check=True, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"[ERRO] Comando expirou após {timeout}s")
        raise
    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Comando falhou: {e}")
        raise

def ensure_ffmpeg():
    """Verifica se FFmpeg está instalado"""
    for bin in ("ffmpeg", "ffprobe"):
        if not shutil.which(bin):
            print(f"[ERRO] {bin} não encontrado no PATH.")
            print("Instale com: sudo apt install ffmpeg")
            sys.exit(1)

def check_rubberband():
    """Verifica se rubberband está disponível"""
    return shutil.which("rubberband") is not None

def ffprobe_duration(path):
    """Obtém duração de arquivo de áudio/vídeo"""
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nk=1:nw=1",
            str(path)
        ], text=True, timeout=30).strip()
        return max(0.0, float(out))
    except Exception:
        return 0.0

def ts_stamp(t):
    """Converte segundos para timestamp SRT"""
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

def get_device():
    """Detecta melhor dispositivo disponível"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"[GPU] Detectada: {gpu_name} ({vram:.1f}GB VRAM)")
            return "cuda"
    except:
        pass
    print("[CPU] Usando CPU (GPU não disponível)")
    return "cpu"

# ============================================================================
# CHECKPOINT SYSTEM
# ============================================================================

def save_checkpoint(workdir, step_num, step_name, data=None):
    """Salva checkpoint da etapa concluída"""
    checkpoint_file = Path(workdir, "checkpoint.json")
    checkpoint = {
        "version": VERSION,
        "last_step": step_name,
        "last_step_num": step_num,
        "next_step": step_num + 1,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)
    print(f"[CHECKPOINT] Etapa {step_num} salva: {step_name}")

def load_checkpoint(workdir):
    """Carrega checkpoint se existir"""
    checkpoint_file = Path(workdir, "checkpoint.json")
    if checkpoint_file.exists():
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# ============================================================================
# ETAPA 3: TRANSCRIÇÃO (WHISPER)
# ============================================================================

def transcribe_faster_whisper(wav_path, workdir, src_lang, model_size="medium"):
    """Transcrição com Faster-Whisper otimizado"""
    print("\n" + "="*60)
    print("=== ETAPA 3: Transcrição (Faster-Whisper) ===")
    print("="*60)

    from faster_whisper import WhisperModel
    import torch

    # Faster-whisper é mais estável em CPU
    device = "cpu"
    compute_type = "int8"

    print(f"[INFO] Whisper modelo: {model_size}")
    print(f"[INFO] Whisper device: {device.upper()} (CTranslate2)")

    if torch.cuda.is_available():
        print(f"[INFO] GPU disponível: {torch.cuda.get_device_name(0)}")
        print(f"[INFO] GPU será usada para M2M100 e TTS")

    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    segments, info = model.transcribe(
        str(wav_path),
        language=src_lang,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=400,
        ),
        beam_size=5,
        best_of=5,
        temperature=0.0,
        condition_on_previous_text=True,
    )

    segs = []
    for s in segments:
        text = (s.text or "").strip()
        if text:  # Ignorar segmentos vazios
            segs.append({
                "start": float(s.start),
                "end": float(s.end),
                "text": text
            })

    # Salvar arquivos
    srt_path = Path(workdir, "asr.srt")
    json_path = Path(workdir, "asr.json")

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{ts_stamp(s['start'])} --> {ts_stamp(s['end'])}\n{s['text']}\n\n")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "language": src_lang,
            "segments": segs,
            "info": {
                "language_probability": getattr(info, 'language_probability', None),
                "duration": getattr(info, 'duration', None),
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"[OK] Transcrito: {len(segs)} segmentos")
    return json_path, srt_path, segs

# ============================================================================
# ETAPA 4: TRADUÇÃO (M2M100 MELHORADO)
# ============================================================================

def proteger_termos_tecnicos(texto):
    """Protege termos técnicos antes da tradução"""
    protegido = texto
    mapa = {}

    for i, termo in enumerate(sorted(TERMOS_PRESERVAR, key=len, reverse=True)):
        # Case-insensitive match
        pattern = re.compile(re.escape(termo), re.IGNORECASE)
        if pattern.search(protegido):
            placeholder = f"__TERMO_{i:03d}__"
            # Preservar o case original
            match = pattern.search(protegido)
            if match:
                mapa[placeholder] = match.group(0)
                protegido = pattern.sub(placeholder, protegido)

    return protegido, mapa

def restaurar_termos_tecnicos(texto, mapa):
    """Restaura termos técnicos após tradução"""
    restaurado = texto
    for placeholder, original in mapa.items():
        restaurado = restaurado.replace(placeholder, original)
    return restaurado

def aplicar_correcoes(texto):
    """Aplica dicionário de correções pós-tradução"""
    corrigido = texto

    # Separar correções em dois grupos:
    # 1. Frases (contém espaço) - substituir direto
    # 2. Palavras únicas - usar word boundary para não quebrar outras palavras

    frases = {k: v for k, v in CORRECOES_TRADUCAO.items() if ' ' in k or "'" in k}
    palavras = {k: v for k, v in CORRECOES_TRADUCAO.items() if ' ' not in k and "'" not in k}

    # Aplicar frases primeiro (mais específicas)
    for errado, correto in frases.items():
        corrigido = corrigido.replace(errado, correto)
        corrigido = corrigido.replace(errado.capitalize(), correto.capitalize())
        corrigido = corrigido.replace(errado.lower(), correto.lower())

    # Aplicar palavras com word boundary
    for errado, correto in palavras.items():
        # Só aplicar se a palavra está isolada (não parte de outra)
        # Usar regex com word boundary
        pattern = re.compile(r'\b' + re.escape(errado) + r'\b', re.IGNORECASE)

        def replace_match(m):
            original = m.group(0)
            # Preservar capitalização
            if original.isupper():
                return correto.upper()
            elif original[0].isupper():
                return correto.capitalize()
            else:
                return correto.lower()

        corrigido = pattern.sub(replace_match, corrigido)

    # Corrigir espaçamento após pontuação
    corrigido = re.sub(r'([.!?])([A-ZÀ-Ú])', r'\1 \2', corrigido)

    # Remover espaços duplicados
    corrigido = re.sub(r' +', ' ', corrigido)

    return corrigido.strip()

def aplicar_glossario(texto, src_lang, tgt_lang):
    """Aplica glossário técnico na tradução"""
    if src_lang != "en" or tgt_lang != "pt":
        return texto

    resultado = texto
    for ingles, portugues in GLOSSARIO_TECNICO.items():
        # Substituir termos em inglês que escaparam
        pattern = re.compile(r'\b' + re.escape(ingles) + r'\b', re.IGNORECASE)
        resultado = pattern.sub(portugues, resultado)

    return resultado

def estimar_duracao_texto(texto, idioma="pt"):
    """Estima duração de fala para um texto"""
    cps = CPS_POR_IDIOMA.get(idioma.lower(), 13)
    return len(texto) / cps

def simplificar_texto(texto, duracao_alvo, idioma="pt"):
    """Simplifica texto se for muito longo para a duração"""
    duracao_estimada = estimar_duracao_texto(texto, idioma)

    if duracao_estimada <= duracao_alvo * 1.2:
        return texto  # OK, não precisa simplificar

    # Estratégias de simplificação
    simplificado = texto

    # 1. Remover palavras de enchimento
    enchimentos = [
        r'\bna verdade\b', r'\bbasicamente\b', r'\bgeralmente\b',
        r'\bsimplesmente\b', r'\brealmente\b', r'\bcertamente\b',
        r'\bobviamente\b', r'\bnaturalmente\b', r'\bprovavelmente\b',
        r'\bpraticamente\b', r'\bexatamente\b', r'\btotalmente\b',
        r'\bcompletamente\b', r'\babsolutamente\b', r'\bdefinitivamente\b',
        r'\bfundamentalmente\b', r'\bessencialmente\b',
        r'\bem outras palavras\b', r'\bou seja\b', r'\bisto é\b',
        r'\bdigamos assim\b', r'\bpor assim dizer\b',
    ]

    for pattern in enchimentos:
        simplificado = re.sub(pattern, '', simplificado, flags=re.IGNORECASE)

    # 2. Remover redundâncias
    redundancias = [
        (r'\bmuito muito\b', 'muito'),
        (r'\bbem bem\b', 'bem'),
        (r'\bmais e mais\b', 'mais'),
        (r'\bcada vez mais e mais\b', 'cada vez mais'),
    ]

    for pattern, replacement in redundancias:
        simplificado = re.sub(pattern, replacement, simplificado, flags=re.IGNORECASE)

    # Limpar espaços extras
    simplificado = re.sub(r' +', ' ', simplificado).strip()

    # Verificar se ainda está muito longo
    nova_duracao = estimar_duracao_texto(simplificado, idioma)
    if nova_duracao > duracao_alvo * 1.3:
        # Truncar preservando sentido
        palavras = simplificado.split()
        palavras_alvo = int(len(palavras) * (duracao_alvo / nova_duracao))
        simplificado = ' '.join(palavras[:palavras_alvo])
        if not simplificado.endswith(('.', '!', '?')):
            simplificado += '.'

    return simplificado

def translate_segments_m2m100(segs, src, tgt, workdir, use_large_model=False):
    """Tradução com M2M100 melhorado"""
    print("\n" + "="*60)
    print("=== ETAPA 4: Tradução (M2M100 Melhorado) ===")
    print("="*60)

    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    import torch

    # Escolher modelo baseado em VRAM disponível
    device = get_device()

    if use_large_model and device == "cuda":
        try:
            vram = torch.cuda.get_device_properties(0).total_memory / 1e9
            if vram >= 6:  # Precisa de ~6GB para o modelo grande
                model_name = "facebook/m2m100_1.2B"
                print(f"[INFO] Usando modelo GRANDE: {model_name} (melhor qualidade)")
            else:
                model_name = "facebook/m2m100_418M"
                print(f"[INFO] VRAM insuficiente para modelo grande, usando: {model_name}")
        except:
            model_name = "facebook/m2m100_418M"
    else:
        model_name = "facebook/m2m100_418M"
        print(f"[INFO] Usando modelo: {model_name}")

    print(f"[INFO] Device: {device.upper()}")

    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)

    # Normalizar códigos de idioma
    src = (src or "en").lower()
    tgt = (tgt or "pt").lower()

    if hasattr(tok, "lang_code_to_id"):
        if src not in tok.lang_code_to_id:
            src = "en"
        if tgt not in tok.lang_code_to_id:
            tgt = "pt"

    out = []
    batch = []
    idxs = []
    mapas_termos = []  # Guardar mapeamento de termos protegidos
    max_batch = 16 if device == "cuda" else 8

    def flush():
        nonlocal out, batch, idxs, mapas_termos
        if not batch:
            return

        tok.src_lang = src
        enc = tok(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
        enc = {k: v.to(device) for k, v in enc.items()}

        gen = model.generate(
            **enc,
            forced_bos_token_id=tok.get_lang_id(tgt),
            max_new_tokens=256,
            num_beams=5,
            length_penalty=1.0,
            early_stopping=True,
        )

        texts = tok.batch_decode(gen, skip_special_tokens=True)

        for j, txt in enumerate(texts):
            i = idxs[j]
            item = dict(segs[i])

            # Restaurar termos técnicos
            txt_restaurado = restaurar_termos_tecnicos(txt, mapas_termos[j])

            # Aplicar correções
            txt_corrigido = aplicar_correcoes(txt_restaurado)

            # Aplicar glossário
            txt_final = aplicar_glossario(txt_corrigido, src, tgt)

            # Calcular duração disponível
            duracao_seg = item["end"] - item["start"]

            # Simplificar se muito longo
            txt_final = simplificar_texto(txt_final, duracao_seg, tgt)

            item["text_trad"] = txt_final
            item["text_original"] = segs[i].get("text", "")
            out.append(item)

        batch.clear()
        idxs.clear()
        mapas_termos.clear()

    print(f"[INFO] Traduzindo {len(segs)} segmentos...")

    for i, s in enumerate(segs):
        texto_original = s.get("text", "")

        # Proteger termos técnicos
        texto_protegido, mapa = proteger_termos_tecnicos(texto_original)

        batch.append(texto_protegido)
        idxs.append(i)
        mapas_termos.append(mapa)

        if len(batch) >= max_batch:
            flush()
            print(f"  Progresso: {len(out)}/{len(segs)}")

    flush()

    # Salvar arquivos
    srt_t = Path(workdir, "asr_trad.srt")
    json_t = Path(workdir, "asr_trad.json")

    with open(srt_t, "w", encoding="utf-8") as f:
        for i, s in enumerate(out, 1):
            f.write(f"{i}\n{ts_stamp(s['start'])} --> {ts_stamp(s['end'])}\n{s['text_trad']}\n\n")

    with open(json_t, "w", encoding="utf-8") as f:
        json.dump({
            "language": tgt,
            "source_language": src,
            "model": model_name,
            "segments": out
        }, f, ensure_ascii=False, indent=2)

    print(f"[OK] Traduzido: {len(out)} segmentos")

    # Liberar memória
    del model
    if device == "cuda":
        import torch
        torch.cuda.empty_cache()

    return out, json_t, srt_t

# ============================================================================
# ETAPA 5: SPLIT INTELIGENTE
# ============================================================================

def split_long_segments(segments, maxdur):
    """Divide segmentos longos de forma inteligente"""
    print("\n" + "="*60)
    print("=== ETAPA 5: Split Inteligente ===")
    print("="*60)

    if not maxdur or maxdur <= 0:
        print("[INFO] Split desativado")
        return segments

    out = []
    split_count = 0

    for seg_idx, s in enumerate(segments, 1):
        start, end = s["start"], s["end"]
        text = (s.get("text_trad") or "").strip()
        dur = max(0.001, end - start)

        # Não dividir se duração OK ou texto curto
        if dur <= maxdur or len(text.split()) < 12:
            out.append(s)
            continue

        print(f"[SPLIT] Seg {seg_idx}: {dur:.2f}s, {len(text)} chars")

        # Dividir por pontuação
        parts = re.split(r'([.!?:;,…])', text)
        cps = max(len(text) / dur, 8.0)

        def is_valid(t):
            t2 = re.sub(r"\s+", " ", (t or "")).strip()
            return len(re.findall(r"[A-Za-zÀ-ÿ0-9]", t2)) >= 3

        # Reconstruir em pedaços
        buf = ""
        pieces = []

        for chunk in parts:
            if chunk is None:
                continue
            cand = (buf + chunk).strip()
            est = len(cand) / cps if cand else 0

            if cand and est > maxdur and is_valid(buf):
                pieces.append(buf.strip())
                buf = chunk.strip()
            else:
                buf = cand

        if is_valid(buf):
            pieces.append(buf.strip())

        if not pieces:
            out.append(s)
            continue

        # Distribuir timestamps proporcionalmente
        total_chars = sum(len(p) for p in pieces)
        cur = start

        for i, piece in enumerate(pieces):
            piece_ratio = len(piece) / total_chars
            piece_dur = dur * piece_ratio
            nxt = cur + piece_dur

            if i == len(pieces) - 1:
                nxt = end

            out.append({
                "start": cur,
                "end": nxt,
                "text_trad": piece,
                "text_original": s.get("text_original", ""),
            })
            cur = nxt

        split_count += 1

    print(f"[OK] Resultado: {len(out)} segmentos ({split_count} divididos)")
    return out

# ============================================================================
# ETAPA 6: TTS (BARK OTIMIZADO + MULTI-PASS)
# ============================================================================

def tts_bark_optimized(segments, workdir, text_temp=0.7, wave_temp=0.5,
                       history_prompt=None, max_retries=2):
    """TTS com Bark otimizado e multi-pass retry"""
    print("\n" + "="*60)
    print("=== ETAPA 6: TTS (Bark Otimizado) ===")
    print("="*60)

    import os
    import torch

    # Patch para PyTorch 2.6+
    print("[INFO] Aplicando patch para compatibilidade PyTorch 2.6+...")

    _original_torch_load = torch.load

    def _patched_torch_load(f, map_location=None, *args, **kwargs):
        kwargs['weights_only'] = False
        return _original_torch_load(f, map_location=map_location, *args, **kwargs)

    torch.load = _patched_torch_load

    from bark import generate_audio, SAMPLE_RATE
    from scipy.io.wavfile import write

    device = get_device()
    print(f"[INFO] Bark device: {device.upper()}")
    print(f"[INFO] Parâmetros otimizados: text_temp={text_temp}, wave_temp={wave_temp}")

    if device == "cuda":
        os.environ['SUNO_USE_SMALL_MODELS'] = '0'
        os.environ['SUNO_OFFLOAD_CPU'] = '0'

    # Carregar history prompt se especificado
    history = None
    if history_prompt:
        try:
            from bark.generation import load_history_prompt
            history = load_history_prompt(history_prompt)
            print(f"[INFO] Usando voz: {history_prompt}")
        except Exception as e:
            print(f"[WARN] Não foi possível carregar voz {history_prompt}: {e}")
            history = history_prompt

    seg_files = []
    metricas = []

    tsv = Path(workdir, "segments.csv")
    with open(tsv, "w", encoding="utf-8", newline="") as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(["idx", "t_in", "t_out", "target_dur", "actual_dur",
                        "ratio", "retries", "texto_trad", "file"])

        for i, s in enumerate(segments, 1):
            txt = (s.get("text_trad") or "").strip()
            target_dur = s["end"] - s["start"]

            # Texto mínimo para evitar erros
            if len(re.findall(r"[A-Za-zÀ-ÿ0-9]", txt)) < 3:
                txt = "pausa curta"

            out_path = Path(workdir, f"seg_{i:04d}.wav")

            # Multi-pass TTS com retry
            best_audio = None
            best_dur = float('inf')
            best_ratio = float('inf')
            retries_used = 0

            for attempt in range(max_retries + 1):
                # Ajustar temperatura baseado na tentativa
                current_text_temp = max(0.4, text_temp - attempt * 0.1)
                current_wave_temp = max(0.3, wave_temp - attempt * 0.1)

                try:
                    audio = generate_audio(
                        txt,
                        history_prompt=history,
                        text_temp=current_text_temp,
                        waveform_temp=current_wave_temp
                    )

                    actual_dur = len(audio) / SAMPLE_RATE
                    ratio = actual_dur / target_dur if target_dur > 0 else 1.0

                    # Verificar se está dentro do aceitável
                    if ratio <= 1.3:  # Até 30% mais longo é OK
                        best_audio = audio
                        best_dur = actual_dur
                        best_ratio = ratio
                        break

                    # Guardar o melhor resultado até agora
                    if abs(ratio - 1.0) < abs(best_ratio - 1.0):
                        best_audio = audio
                        best_dur = actual_dur
                        best_ratio = ratio

                    retries_used = attempt + 1

                    if attempt < max_retries:
                        print(f"  [RETRY] Seg {i}: {actual_dur:.2f}s vs alvo {target_dur:.2f}s ({ratio:.1%})")

                except Exception as e:
                    print(f"  [ERRO] Seg {i} tentativa {attempt+1}: {e}")
                    if attempt == max_retries:
                        # Gerar silêncio como fallback
                        best_audio = np.zeros(int(target_dur * SAMPLE_RATE), dtype=np.float32)
                        best_dur = target_dur
                        best_ratio = 1.0

            # Salvar melhor resultado - NORMALIZAR ÁUDIO para evitar clipping
            # O Bark pode gerar valores > 1.0, que causam problemas no FFmpeg
            if best_audio is not None:
                # Normalizar para [-1, 1]
                max_val = np.max(np.abs(best_audio))
                if max_val > 1.0:
                    best_audio = best_audio / max_val * 0.95  # 95% para headroom

                # Converter para int16 para melhor compatibilidade
                audio_int16 = (best_audio * 32767).astype(np.int16)
                write(out_path, SAMPLE_RATE, audio_int16)
            else:
                # Silêncio como fallback
                audio_int16 = np.zeros(int(target_dur * SAMPLE_RATE), dtype=np.int16)
                write(out_path, SAMPLE_RATE, audio_int16)

            seg_files.append(out_path)

            # Métricas
            metricas.append({
                "idx": i,
                "target": target_dur,
                "actual": best_dur,
                "ratio": best_ratio,
                "retries": retries_used
            })

            writer.writerow([i, s["start"], s["end"], f"{target_dur:.3f}",
                           f"{best_dur:.3f}", f"{best_ratio:.3f}", retries_used,
                           txt[:50], out_path.name])

            # Progresso
            if i % 10 == 0 or i == len(segments):
                print(f"  Progresso: {i}/{len(segments)}")

    # Restaurar torch.load
    torch.load = _original_torch_load

    # Estatísticas
    ratios = [m["ratio"] for m in metricas]
    print(f"\n[STATS] TTS Bark:")
    print(f"  Segmentos: {len(seg_files)}")
    print(f"  Ratio médio: {np.mean(ratios):.2%}")
    print(f"  Ratio min/max: {np.min(ratios):.2%} / {np.max(ratios):.2%}")
    print(f"  Retries totais: {sum(m['retries'] for m in metricas)}")

    return seg_files, SAMPLE_RATE, metricas

def tts_coqui_optimized(segments, workdir, tgt_lang, speaker=None):
    """TTS com Coqui - NOTA: Requer Python < 3.12"""
    print("\n" + "="*60)
    print("=== ETAPA 6: TTS (Coqui) ===")
    print("="*60)

    # Verificar se TTS está disponível
    try:
        from TTS.api import TTS
    except ImportError:
        print("[ERRO] Coqui TTS não está instalado ou não suporta esta versão do Python")
        print("[INFO] Python 3.13+ não é suportado pelo Coqui TTS")
        print("[INFO] Alternativas:")
        print("       1. Use --tts bark (recomendado)")
        print("       2. Use Python 3.11 para Coqui TTS")
        sys.exit(1)

    import torch

    lang = (tgt_lang or "en").lower()
    device = get_device()

    # Escolher modelo baseado no idioma
    if lang in ("pt", "pt-br", "pt_pt"):
        model_name = "tts_models/pt/cv/vits"
        sample_rate = 22050
    elif lang in ("es", "es-es", "es-mx"):
        model_name = "tts_models/es/css10/vits"
        sample_rate = 22050
    else:
        model_name = "tts_models/en/ljspeech/tacotron2-DDC"
        sample_rate = 22050

    print(f"[INFO] Modelo: {model_name}")
    print(f"[INFO] Device: {device.upper()}")

    tts = TTS(model_name, gpu=(device == "cuda"))

    seg_files = []
    tsv = Path(workdir, "segments.csv")

    with open(tsv, "w", encoding="utf-8", newline="") as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(["idx", "t_in", "t_out", "texto_trad", "file"])

        for i, s in enumerate(segments, 1):
            txt = (s.get("text_trad") or "").strip()

            if len(re.findall(r"[A-Za-zÀ-ÿ0-9]", txt)) < 3:
                txt = "pausa curta"

            out_path = Path(workdir, f"seg_{i:04d}.wav")

            try:
                if speaker:
                    tts.tts_to_file(text=txt, file_path=str(out_path),
                                  speaker=speaker, language=tgt_lang)
                else:
                    tts.tts_to_file(text=txt, file_path=str(out_path))
            except Exception as e:
                print(f"  [ERRO] Seg {i}: {e}")
                # Fallback sem speaker
                tts.tts_to_file(text=txt, file_path=str(out_path))

            seg_files.append(out_path)
            writer.writerow([i, s["start"], s["end"], txt[:50], out_path.name])

            if i % 10 == 0 or i == len(segments):
                print(f"  Progresso: {i}/{len(segments)}")

    print(f"[OK] TTS Coqui: {len(seg_files)} segmentos")
    return seg_files, sample_rate, []


def tts_edge(segments, workdir, tgt_lang, voice=None):
    """TTS com Edge TTS (Microsoft) - Vozes consistentes e de alta qualidade

    Requer internet. Vozes disponíveis para pt-BR:
    - pt-BR-AntonioNeural (masculina)
    - pt-BR-FranciscaNeural (feminina)
    - pt-BR-HumbertoNeural (masculina)
    """
    print("\n" + "="*60)
    print("=== ETAPA 6: TTS (Edge TTS - Microsoft) ===")
    print("="*60)

    import asyncio
    import edge_tts
    from scipy.io import wavfile
    import subprocess

    # Mapear idioma para voz padrão
    VOZES_PADRAO = {
        "pt": "pt-BR-AntonioNeural",
        "pt-br": "pt-BR-AntonioNeural",
        "pt_br": "pt-BR-AntonioNeural",
        "en": "en-US-GuyNeural",
        "en-us": "en-US-GuyNeural",
        "en-gb": "en-GB-RyanNeural",
        "es": "es-ES-AlvaroNeural",
        "es-es": "es-ES-AlvaroNeural",
        "es-mx": "es-MX-JorgeNeural",
        "fr": "fr-FR-HenriNeural",
        "de": "de-DE-ConradNeural",
        "it": "it-IT-DiegoNeural",
        "ja": "ja-JP-KeitaNeural",
        "zh": "zh-CN-YunxiNeural",
        "ko": "ko-KR-InJoonNeural",
    }

    lang = (tgt_lang or "pt").lower().replace("_", "-")
    selected_voice = voice or VOZES_PADRAO.get(lang, "pt-BR-AntonioNeural")

    print(f"[INFO] Voz: {selected_voice}")
    print(f"[INFO] Idioma: {lang}")

    # Sample rate do Edge TTS é 24000
    SAMPLE_RATE = 24000

    seg_files = []
    tsv = Path(workdir, "segments.csv")

    async def generate_audio(text, output_path):
        """Gera áudio usando Edge TTS"""
        communicate = edge_tts.Communicate(text, selected_voice)
        # Edge TTS gera MP3, precisamos converter para WAV
        mp3_path = str(output_path).replace(".wav", ".mp3")
        await communicate.save(mp3_path)

        # Converter MP3 para WAV
        subprocess.run([
            "ffmpeg", "-y", "-i", mp3_path,
            "-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", "pcm_s16le",
            str(output_path)
        ], capture_output=True)

        # Remover MP3 temporário
        if os.path.exists(mp3_path):
            os.remove(mp3_path)

        return output_path

    async def process_all_segments():
        """Processa todos os segmentos"""
        tasks = []

        with open(tsv, "w", encoding="utf-8", newline="") as fcsv:
            writer = csv.writer(fcsv)
            writer.writerow(["idx", "t_in", "t_out", "texto_trad", "file"])

            for i, s in enumerate(segments, 1):
                txt = (s.get("text_trad") or "").strip()

                # Texto mínimo
                if len(re.findall(r"[A-Za-zÀ-ÿ0-9]", txt)) < 3:
                    txt = "pausa"

                out_path = Path(workdir, f"seg_{i:04d}.wav")

                try:
                    await generate_audio(txt, out_path)
                    seg_files.append(out_path)
                except Exception as e:
                    print(f"  [ERRO] Seg {i}: {e}")
                    # Criar silêncio como fallback
                    dur = s.get("end", 1) - s.get("start", 0)
                    silence = np.zeros(int(dur * SAMPLE_RATE), dtype=np.int16)
                    wavfile.write(str(out_path), SAMPLE_RATE, silence)
                    seg_files.append(out_path)

                writer.writerow([i, s["start"], s["end"], txt[:50], out_path.name])

                if i % 5 == 0 or i == len(segments):
                    print(f"  Progresso: {i}/{len(segments)}")

    # Executar processamento assíncrono
    asyncio.run(process_all_segments())

    print(f"[OK] TTS Edge: {len(seg_files)} segmentos")
    return seg_files, SAMPLE_RATE, []


def tts_piper(segments, workdir, tgt_lang, model_path=None):
    """TTS com Piper - Offline, leve e rápido

    Requer download de modelo de voz.
    Modelos pt-BR: https://github.com/rhasspy/piper/releases
    """
    print("\n" + "="*60)
    print("=== ETAPA 6: TTS (Piper - Offline) ===")
    print("="*60)

    from scipy.io import wavfile
    import subprocess

    # Verificar se modelo existe
    if not model_path:
        # Tentar encontrar modelo padrão
        default_paths = [
            Path.home() / ".local/share/piper/pt_BR-faber-medium.onnx",
            Path.home() / "piper-models/pt_BR-faber-medium.onnx",
            Path("models/piper/pt_BR-faber-medium.onnx"),
        ]
        for p in default_paths:
            if p.exists():
                model_path = str(p)
                break

    if not model_path or not Path(model_path).exists():
        print("[ERRO] Modelo Piper não encontrado!")
        print("[INFO] Baixe um modelo pt-BR de:")
        print("       https://github.com/rhasspy/piper/releases")
        print("[INFO] E use: --voice /caminho/para/modelo.onnx")
        print("[INFO] Ou instale com:")
        print("       mkdir -p ~/.local/share/piper")
        print("       wget -O ~/.local/share/piper/pt_BR-faber-medium.onnx \\")
        print("         https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx")
        sys.exit(1)

    print(f"[INFO] Modelo: {model_path}")

    SAMPLE_RATE = 22050  # Piper usa 22050 por padrão

    seg_files = []
    tsv = Path(workdir, "segments.csv")

    with open(tsv, "w", encoding="utf-8", newline="") as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(["idx", "t_in", "t_out", "texto_trad", "file"])

        for i, s in enumerate(segments, 1):
            txt = (s.get("text_trad") or "").strip()

            if len(re.findall(r"[A-Za-zÀ-ÿ0-9]", txt)) < 3:
                txt = "pausa"

            out_path = Path(workdir, f"seg_{i:04d}.wav")

            try:
                # Piper lê do stdin
                proc = subprocess.run(
                    ["piper", "-m", model_path, "-f", str(out_path)],
                    input=txt.encode("utf-8"),
                    capture_output=True
                )

                if proc.returncode != 0:
                    raise Exception(proc.stderr.decode())

            except Exception as e:
                print(f"  [ERRO] Seg {i}: {e}")
                # Criar silêncio como fallback
                dur = s.get("end", 1) - s.get("start", 0)
                silence = np.zeros(int(dur * SAMPLE_RATE), dtype=np.int16)
                wavfile.write(str(out_path), SAMPLE_RATE, silence)

            seg_files.append(out_path)
            writer.writerow([i, s["start"], s["end"], txt[:50], out_path.name])

            if i % 10 == 0 or i == len(segments):
                print(f"  Progresso: {i}/{len(segments)}")

    print(f"[OK] TTS Piper: {len(seg_files)} segmentos")
    return seg_files, SAMPLE_RATE, []


# ============================================================================
# ETAPA 6.1: FADE
# ============================================================================

def apply_fade(seg_files, workdir, fade_in=0.01, fade_out=0.01):
    """Aplica fade-in e fade-out nos segmentos usando NumPy

    NOTA: FFmpeg afade tem bug em algumas plataformas ARM64,
    por isso usamos NumPy para aplicar o fade.
    """
    print("\n=== ETAPA 6.1: Aplicando Fade ===")
    from scipy.io import wavfile as wf

    xf_files = []
    for p in seg_files:
        out = Path(workdir, p.name.replace(".wav", "_xf.wav"))

        try:
            sr, data = wf.read(str(p))

            # Converter para float para processamento
            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32767.0
            elif data.dtype == np.int32:
                data = data.astype(np.float32) / 2147483647.0

            # Calcular amostras de fade
            fade_in_samples = int(fade_in * sr)
            fade_out_samples = int(fade_out * sr)

            # Aplicar fade-in
            if fade_in_samples > 0 and fade_in_samples < len(data):
                fade_in_curve = np.linspace(0, 1, fade_in_samples)
                data[:fade_in_samples] *= fade_in_curve

            # Aplicar fade-out
            if fade_out_samples > 0 and fade_out_samples < len(data):
                fade_out_curve = np.linspace(1, 0, fade_out_samples)
                data[-fade_out_samples:] *= fade_out_curve

            # Converter de volta para int16
            data_int16 = (data * 32767).astype(np.int16)
            wf.write(str(out), sr, data_int16)

        except Exception as e:
            print(f"  [WARN] Fade falhou para {p.name}: {e}, copiando sem fade")
            import shutil
            shutil.copy(str(p), str(out))

        xf_files.append(out)

    print(f"[OK] Fade aplicado: {len(xf_files)} segmentos")
    return xf_files

# ============================================================================
# ETAPA 7: SINCRONIZAÇÃO AVANÇADA
# ============================================================================

def atempo_chain(factor):
    """Gera cadeia de filtros atempo para fatores extremos"""
    chain = []
    f = float(factor)

    while f < 0.5:
        chain.append("atempo=0.5")
        f /= 0.5
    while f > 2.0:
        chain.append("atempo=2.0")
        f /= 2.0

    chain.append(f"atempo={f:.6f}")
    return ",".join(chain)

def time_stretch_rubberband(input_path, output_path, ratio):
    """Time-stretch com rubberband (preserva pitch)"""
    if not check_rubberband():
        return False

    try:
        sh(["rubberband",
            "-t", str(ratio),
            "-p", "0",  # Preservar pitch
            "--crisp", "5",  # Alta qualidade
            str(input_path),
            str(output_path)])
        return True
    except:
        return False

def sync_fit_advanced(p, target, workdir, sr, tol, maxstretch, use_rubberband=True):
    """Sincronização fit avançada com opção de rubberband ou librosa"""
    from scipy.io import wavfile as wf

    cur = ffprobe_duration(p)
    if cur <= 0:
        return p

    ratio = target / cur

    # Verificar se precisa ajuste
    if abs(ratio - 1.0) < tol:
        return p

    # Limitar ratio
    ratio = max(min(ratio, maxstretch), 1.0 / maxstretch)

    out = Path(workdir, p.name.replace(".wav", "_fit.wav"))

    # Tentar rubberband primeiro (melhor qualidade)
    if use_rubberband and check_rubberband():
        if time_stretch_rubberband(p, out, ratio):
            print(f"    [FIT-RB] {cur:.2f}s → {target:.2f}s (ratio={ratio:.3f})")
            # Verificar e corrigir formato
            try:
                file_sr, data = wf.read(str(out))
                if data.dtype != np.int16:
                    if data.dtype in [np.float32, np.float64]:
                        max_val = np.max(np.abs(data))
                        if max_val > 1.0:
                            data = data / max_val * 0.95
                        data = (data * 32767).astype(np.int16)
                    wf.write(str(out), file_sr, data)
            except:
                pass
            return out

    # Fallback usando librosa time_stretch
    print(f"    [FIT-LB] {cur:.2f}s → {target:.2f}s (ratio={ratio:.3f})")
    try:
        import librosa

        file_sr, data = wf.read(str(p))

        # Converter para float
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32767.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483647.0

        # Time stretch com librosa (rate = 1/ratio para obter a duração desejada)
        # Se ratio < 1, precisamos esticar (rate < 1)
        # Se ratio > 1, precisamos comprimir (rate > 1)
        stretched = librosa.effects.time_stretch(data, rate=1.0/ratio)

        # Ajustar para exatamente o target
        target_samples = int(target * file_sr)
        if len(stretched) > target_samples:
            stretched = stretched[:target_samples]
        elif len(stretched) < target_samples:
            pad = np.zeros(target_samples - len(stretched), dtype=np.float32)
            stretched = np.concatenate([stretched, pad])

        # Normalizar e converter para int16
        max_val = np.max(np.abs(stretched))
        if max_val > 0:
            stretched = stretched / max_val * 0.95

        data_int16 = (stretched * 32767).astype(np.int16)
        wf.write(str(out), file_sr, data_int16)
        return out

    except Exception as e:
        print(f"    [WARN] time_stretch falhou: {e}, mantendo original")
        return p

def sync_pad(p, target, workdir, sr):
    """Sincronização com padding usando NumPy

    NOTA: FFmpeg apad/atrim tem bugs em ARM64, usando NumPy.
    """
    from scipy.io import wavfile as wf

    cur = ffprobe_duration(p)
    if cur <= 0:
        return p

    out = Path(workdir, p.name.replace(".wav", "_pad.wav"))

    try:
        file_sr, data = wf.read(str(p))

        # Converter para float se necessário
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32767.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483647.0

        target_samples = int(target * file_sr)

        if len(data) >= target_samples:
            # Cortar
            print(f"    [PAD-CUT] {cur:.2f}s → {target:.2f}s")
            data = data[:target_samples]
        else:
            # Adicionar silêncio
            pad_samples = target_samples - len(data)
            pad_dur = pad_samples / file_sr
            print(f"    [PAD-ADD] {cur:.2f}s + {pad_dur:.2f}s = {target:.2f}s")
            silence = np.zeros(pad_samples, dtype=np.float32)
            data = np.concatenate([data, silence])

        # Converter de volta para int16
        data_int16 = (data * 32767).astype(np.int16)
        wf.write(str(out), file_sr, data_int16)
        return out

    except Exception as e:
        print(f"    [WARN] sync_pad falhou: {e}")
        return p

def sync_smart_advanced(p, target, workdir, sr, tol, maxstretch, use_rubberband=True):
    """Sincronização smart avançada"""
    cur = ffprobe_duration(p)
    if cur <= 0:
        return p

    low = target * (1 - tol)
    high = target * (1 + tol)

    print(f"  [SYNC] {p.name}: alvo={target:.2f}s, atual={cur:.2f}s, range=[{low:.2f}s-{high:.2f}s]")

    if cur < low:
        print(f"  [SYNC] → PAD (muito curto)")
        return sync_pad(p, target, workdir, sr)
    elif cur > high:
        print(f"  [SYNC] → FIT (muito longo)")
        return sync_fit_advanced(p, target, workdir, sr, tol, maxstretch, use_rubberband)
    else:
        print(f"  [SYNC] → OK")
        return p

# ============================================================================
# ETAPA 8: CONCATENAÇÃO
# ============================================================================

def concat_segments(seg_files, workdir, samplerate):
    """Concatena segmentos de áudio"""
    print("\n" + "="*60)
    print("=== ETAPA 8: Concatenação ===")
    print("="*60)

    lst = Path(workdir, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in seg_files:
            f.write(f"file '{p.name}'\n")

    out = Path(workdir, "dub_raw.wav")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-c:a", "pcm_s16le", "-ar", str(samplerate), "-ac", "1",
        str(out)])

    print(f"[OK] Concatenado: {out.name}")
    return out

# ============================================================================
# ETAPA 9: PÓS-PROCESSAMENTO
# ============================================================================

def postprocess_audio(wav_in, workdir, samplerate):
    """Pós-processamento do áudio final usando NumPy

    NOTA: FFmpeg loudnorm tem bug em ARM64, usando normalização simples.
    """
    print("\n" + "="*60)
    print("=== ETAPA 9: Pós-processamento ===")
    print("="*60)

    from scipy.io import wavfile as wf

    out = Path(workdir, "dub_final.wav")

    try:
        file_sr, data = wf.read(str(wav_in))

        # Converter para float
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32767.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483647.0

        # Normalização simples (peak normalization com headroom)
        max_val = np.max(np.abs(data))
        if max_val > 0:
            # Normalizar para -1.5dB de headroom (≈ 0.84)
            target_peak = 0.84
            data = data / max_val * target_peak
            print(f"  [NORM] Pico original: {max_val:.4f}, normalizado para: {target_peak:.2f}")

        # Converter para int16
        data_int16 = (data * 32767).astype(np.int16)
        wf.write(str(out), file_sr, data_int16)

        print(f"[OK] Pós-processado: {out.name}")

    except Exception as e:
        print(f"[WARN] Pós-processamento falhou: {e}, copiando original")
        import shutil
        shutil.copy(str(wav_in), str(out))

    return out

# ============================================================================
# ETAPA 10: MUX FINAL
# ============================================================================

def mux_video(video_in, wav_in, out_mp4, bitrate):
    """Combina vídeo original com áudio dublado"""
    print("\n" + "="*60)
    print("=== ETAPA 10: Mux Final ===")
    print("="*60)

    sh(["ffmpeg", "-y",
        "-i", str(video_in),
        "-i", str(wav_in),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", bitrate,
        str(out_mp4)])

    print(f"[OK] Vídeo final: {out_mp4}")

# ============================================================================
# MÉTRICAS DE QUALIDADE
# ============================================================================

def calculate_quality_metrics(segments, seg_files, workdir):
    """Calcula métricas de qualidade da dublagem"""
    print("\n" + "="*60)
    print("=== Métricas de Qualidade ===")
    print("="*60)

    metricas = {
        "total_segments": len(segments),
        "sync_stats": {
            "within_5pct": 0,
            "within_10pct": 0,
            "within_20pct": 0,
            "over_20pct": 0,
        },
        "translation_stats": {
            "avg_compression": 0,
            "chars_original": 0,
            "chars_translated": 0,
        }
    }

    total_ratio = 0

    for i, (seg, seg_file) in enumerate(zip(segments, seg_files)):
        target_dur = seg["end"] - seg["start"]
        actual_dur = ffprobe_duration(seg_file)

        if target_dur > 0:
            ratio = actual_dur / target_dur
            diff = abs(ratio - 1.0)

            if diff <= 0.05:
                metricas["sync_stats"]["within_5pct"] += 1
            elif diff <= 0.10:
                metricas["sync_stats"]["within_10pct"] += 1
            elif diff <= 0.20:
                metricas["sync_stats"]["within_20pct"] += 1
            else:
                metricas["sync_stats"]["over_20pct"] += 1

            total_ratio += ratio

        # Estatísticas de tradução
        orig = seg.get("text_original", "")
        trad = seg.get("text_trad", "")
        metricas["translation_stats"]["chars_original"] += len(orig)
        metricas["translation_stats"]["chars_translated"] += len(trad)

    if len(segments) > 0:
        metricas["sync_stats"]["avg_ratio"] = total_ratio / len(segments)

    if metricas["translation_stats"]["chars_original"] > 0:
        metricas["translation_stats"]["avg_compression"] = (
            metricas["translation_stats"]["chars_translated"] /
            metricas["translation_stats"]["chars_original"]
        )

    # Imprimir resumo
    print(f"  Segmentos totais: {metricas['total_segments']}")
    print(f"  Sincronização:")
    print(f"    - Dentro de 5%: {metricas['sync_stats']['within_5pct']}")
    print(f"    - Dentro de 10%: {metricas['sync_stats']['within_10pct']}")
    print(f"    - Dentro de 20%: {metricas['sync_stats']['within_20pct']}")
    print(f"    - Acima de 20%: {metricas['sync_stats']['over_20pct']}")
    print(f"  Tradução:")
    print(f"    - Compressão média: {metricas['translation_stats']['avg_compression']:.2%}")

    # Salvar métricas
    metrics_file = Path(workdir, "quality_metrics.json")
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)

    return metricas

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*60)
    print(f"  inemaVOX v{VERSION}")
    print("  Pipeline de Dublagem Profissional")
    print("="*60)

    ap = argparse.ArgumentParser(
        description="Dublagem profissional com Whisper + M2M100 + Bark/Coqui",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python dublar_pro.py --in video.mp4 --src en --tgt pt
  python dublar_pro.py --in video.mp4 --src en --tgt pt --tts coqui --large-model
  python dublar_pro.py --in video.mp4 --src en --tgt pt --sync smart --tolerance 0.1
        """
    )

    # Argumentos obrigatórios
    ap.add_argument("--in", dest="inp", required=True, help="Vídeo de entrada")
    ap.add_argument("--src", required=True, help="Idioma de origem (en, es, fr, etc)")
    ap.add_argument("--tgt", required=True, help="Idioma de destino (pt, en, es, etc)")

    # Saída
    ap.add_argument("--out", dest="out", default=None, help="Vídeo de saída (default: video_dublado.mp4)")
    ap.add_argument("--outdir", default="dublado", help="Diretório de saída (default: dublado)")

    # TTS
    ap.add_argument("--tts", choices=["bark", "coqui", "edge", "piper"], default="bark",
                   help="Engine TTS: bark (offline), edge (online, consistente), piper (offline, leve), coqui")
    ap.add_argument("--voice", default=None,
                   help="Voz TTS. Edge: pt-BR-AntonioNeural, pt-BR-FranciscaNeural. Bark: v2/pt_speaker_1..5")
    ap.add_argument("--texttemp", type=float, default=0.7, help="Bark text temperature (default: 0.7)")
    ap.add_argument("--wavetemp", type=float, default=0.5, help="Bark waveform temperature (default: 0.5)")
    ap.add_argument("--max-retries", type=int, default=2, help="Max retries TTS (default: 2)")

    # Tradução
    ap.add_argument("--large-model", action="store_true", help="Usar M2M100 1.2B (melhor qualidade, mais VRAM)")
    ap.add_argument("--whisper-model", default="medium", choices=["tiny", "small", "medium", "large"],
                   help="Modelo Whisper (default: medium)")

    # Sincronização
    ap.add_argument("--sync", choices=["none", "fit", "pad", "smart"], default="smart",
                   help="Modo de sincronização (default: smart)")
    ap.add_argument("--tolerance", type=float, default=0.1, help="Tolerância sync (default: 0.1 = 10%%)")
    ap.add_argument("--maxstretch", type=float, default=1.4, help="Max compressão/expansão (default: 1.4)")
    ap.add_argument("--use-rubberband", action="store_true", help="Usar rubberband para time-stretch")

    # Outros
    ap.add_argument("--maxdur", type=float, default=10.0, help="Duração máxima de segmento (default: 10s)")
    ap.add_argument("--rate", type=int, default=24000, help="Sample rate final (default: 24000)")
    ap.add_argument("--bitrate", default="192k", help="Bitrate AAC (default: 192k)")
    ap.add_argument("--fade", type=int, default=1, choices=[0, 1], help="Aplicar fade (default: 1)")
    ap.add_argument("--resume", action="store_true", help="Continuar de checkpoint")

    args = ap.parse_args()

    # Verificações
    ensure_ffmpeg()

    video_in = Path(args.inp).resolve()
    if not video_in.exists():
        print(f"[ERRO] Arquivo não encontrado: {video_in}")
        sys.exit(1)

    # Diretórios
    workdir = Path("dub_work")
    workdir.mkdir(exist_ok=True)

    outdir = Path(args.outdir)
    outdir.mkdir(exist_ok=True)

    # Nome do arquivo de saída
    if args.out:
        out_mp4 = Path(args.out)
    else:
        out_mp4 = outdir / f"{video_in.stem}_dublado.mp4"

    # Determinar voz a ser usada
    if args.voice:
        display_voice = args.voice
    elif args.tts == "edge":
        display_voice = "pt-BR-AntonioNeural (default)"
    elif args.tts == "piper":
        display_voice = "modelo padrão"
    else:
        display_voice = "v2/pt_speaker_3 (default)"

    print(f"\n[CONFIG]")
    print(f"  Entrada: {video_in}")
    print(f"  Saída: {out_mp4}")
    print(f"  Idiomas: {args.src} → {args.tgt}")
    print(f"  TTS: {args.tts} (voz: {display_voice})")
    print(f"  Sync: {args.sync} (tol: {args.tolerance}, max: {args.maxstretch})")
    print(f"  Modelo grande: {'Sim' if args.large_model else 'Não'}")

    # Verificar rubberband
    if args.use_rubberband:
        if check_rubberband():
            print(f"  Rubberband: Disponível")
        else:
            print(f"  Rubberband: Não instalado (usando atempo)")
            args.use_rubberband = False

    # ========== ETAPA 1: Extração de áudio ==========
    print("\n" + "="*60)
    print("=== ETAPA 1-2: Validação e Extração ===")
    print("="*60)

    audio_src = Path(workdir, "audio_src.wav")
    sh(["ffmpeg", "-y", "-i", str(video_in),
        "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le",
        str(audio_src)])

    save_checkpoint(workdir, 2, "extraction")

    # ========== ETAPA 3: Transcrição ==========
    asr_json, asr_srt, segs = transcribe_faster_whisper(
        audio_src, workdir, args.src, args.whisper_model
    )
    save_checkpoint(workdir, 3, "transcription")

    # ========== ETAPA 4: Tradução ==========
    segs_trad, trad_json, trad_srt = translate_segments_m2m100(
        segs, args.src, args.tgt, workdir, args.large_model
    )
    save_checkpoint(workdir, 4, "translation")

    # ========== ETAPA 5: Split ==========
    segs_trad = split_long_segments(segs_trad, args.maxdur)
    save_checkpoint(workdir, 5, "split")

    # ========== ETAPA 6: TTS ==========
    if args.tts == "bark":
        voice = args.voice or "v2/pt_speaker_3"
        seg_files, sr_segs, tts_metrics = tts_bark_optimized(
            segs_trad, workdir,
            text_temp=args.texttemp,
            wave_temp=args.wavetemp,
            history_prompt=voice,
            max_retries=args.max_retries
        )
    elif args.tts == "edge":
        seg_files, sr_segs, tts_metrics = tts_edge(
            segs_trad, workdir, args.tgt, voice=args.voice
        )
    elif args.tts == "piper":
        seg_files, sr_segs, tts_metrics = tts_piper(
            segs_trad, workdir, args.tgt, model_path=args.voice
        )
    else:  # coqui
        seg_files, sr_segs, tts_metrics = tts_coqui_optimized(
            segs_trad, workdir, args.tgt, speaker=args.voice
        )

    save_checkpoint(workdir, 6, "tts")

    # ========== ETAPA 6.1: Fade ==========
    if args.fade == 1:
        seg_files = apply_fade(seg_files, workdir)

    # ========== ETAPA 7: Sincronização ==========
    print("\n" + "="*60)
    print("=== ETAPA 7: Sincronização ===")
    print("="*60)

    fixed = []
    for i, s in enumerate(segs_trad, 1):
        target = max(0.05, s["end"] - s["start"])
        p = seg_files[i - 1]

        if args.sync == "none":
            fixed.append(p)
        elif args.sync == "fit":
            fixed.append(sync_fit_advanced(p, target, workdir, sr_segs,
                                          args.tolerance, args.maxstretch, args.use_rubberband))
        elif args.sync == "pad":
            fixed.append(sync_pad(p, target, workdir, sr_segs))
        elif args.sync == "smart":
            fixed.append(sync_smart_advanced(p, target, workdir, sr_segs,
                                            args.tolerance, args.maxstretch, args.use_rubberband))

    seg_files = fixed
    save_checkpoint(workdir, 7, "sync")

    # ========== ETAPA 8: Concatenação ==========
    dub_raw = concat_segments(seg_files, workdir, sr_segs)
    save_checkpoint(workdir, 8, "concat")

    # ========== ETAPA 9: Pós-processamento ==========
    dub_final = postprocess_audio(dub_raw, workdir, args.rate)
    save_checkpoint(workdir, 9, "postprocess")

    # ========== ETAPA 10: Mux ==========
    mux_video(video_in, dub_final, out_mp4, args.bitrate)
    save_checkpoint(workdir, 10, "mux")

    # ========== Métricas ==========
    metrics = calculate_quality_metrics(segs_trad, seg_files, workdir)

    # ========== Logs finais ==========
    logs = {
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "input_video": str(video_in),
        "output_video": str(out_mp4),
        "config": {
            "src": args.src,
            "tgt": args.tgt,
            "tts": args.tts,
            "voice": args.voice,
            "sync": args.sync,
            "tolerance": args.tolerance,
            "maxstretch": args.maxstretch,
            "maxdur": args.maxdur,
            "texttemp": args.texttemp,
            "wavetemp": args.wavetemp,
            "fade": args.fade,
            "large_model": args.large_model,
            "whisper_model": args.whisper_model,
            "use_rubberband": args.use_rubberband,
        },
        "files": {
            "asr_json": str(asr_json),
            "asr_srt": str(asr_srt),
            "trad_json": str(trad_json),
            "trad_srt": str(trad_srt),
            "workdir": str(workdir),
        },
        "metrics": metrics,
    }

    with open(Path(workdir, "logs.json"), "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    # ========== Resumo ==========
    print("\n" + "="*60)
    print("  DUBLAGEM CONCLUÍDA!")
    print("="*60)
    print(f"\n  Saídas:")
    print(f"    Vídeo: {out_mp4}")
    print(f"    Legendas: {trad_srt}")
    print(f"    Logs: {workdir}/logs.json")
    print(f"    Métricas: {workdir}/quality_metrics.json")
    print(f"\n  Intermediários em: {workdir}/")
    print("="*60)

if __name__ == "__main__":
    main()
