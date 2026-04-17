"""
Post-procesador de texto transcrito.
Pipeline: siglas → nombres propios → frases → preguntas → listas
"""

import re

# ── 1. Siglas que siempre van en mayúsculas ─────────────────────────────────

_ACRONYMS = [
    # Formatos y protocolos
    "JSON", "CSV", "XML", "YAML", "TOML", "HTML", "CSS",
    "HTTP", "HTTPS", "SSH", "FTP", "TCP", "UDP", "IP", "DNS", "URL", "URI",
    "REST", "SOAP", "API", "SDK", "CLI", "GUI", "UI", "UX",
    # Bases de datos
    "SQL", "BBDD", "DB", "ORM", "CRUD",
    # Infraestructura / cloud
    "AWS", "GCP", "GCV", "CI", "CD", "PR", "MR", "VM",
    # Hardware / sistema
    "CPU", "GPU", "RAM", "SSD", "HDD", "OS", "PC", "MAC",
    # Identificadores / auth
    "ID", "UUID", "JWT", "OAuth", "SSO", "MFA", "2FA",
    # IA / ML
    "IA", "ML", "LLM", "GPT", "RAG", "NLP", "OCR",
    # Redes sociales / marketing
    "RRSS", "SEO", "SEM", "CRM", "ERP", "CTA", "ROI", "KPI",
    # Otros comunes
    "PDF", "QR", "WIP", "MVP", "POC", "TBD", "FAQ",
]

# ── 2. Nombres propios con capitalización específica ────────────────────────

_PROPER_NAMES: dict[str, str] = {
    # Lenguajes
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "python":     "Python",
    "kotlin":     "Kotlin",
    "golang":     "Go",
    "swift":      "Swift",
    "ruby":       "Ruby",
    "java":       "Java",
    "rust":       "Rust",
    # Frameworks / librerías
    "react":      "React",
    "vue":        "Vue",
    "angular":    "Angular",
    "django":     "Django",
    "fastapi":    "FastAPI",
    "nextjs":     "Next.js",
    "nodejs":     "Node.js",
    "tailwind":   "Tailwind",
    # Plataformas / herramientas
    "github":     "GitHub",
    "gitlab":     "GitLab",
    "docker":     "Docker",
    "kubernetes": "Kubernetes",
    "terraform":  "Terraform",
    "ansible":    "Ansible",
    "postgres":   "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongodb":    "MongoDB",
    "redis":      "Redis",
    "elasticsearch": "Elasticsearch",
    "nginx":      "Nginx",
    "linux":      "Linux",
    "macos":      "macOS",
    "iphone":     "iPhone",
    "ipad":       "iPad",
    "vscode":     "VSCode",
    "xcode":      "Xcode",
    # IA
    "chatgpt":    "ChatGPT",
    "openai":     "OpenAI",
    "anthropic":  "Anthropic",
    "claude":     "Claude",
    "gemini":     "Gemini",
    "mistral":    "Mistral",
    # Servicios
    "google":     "Google",
    "microsoft":  "Microsoft",
    "amazon":     "Amazon",
    "netflix":    "Netflix",
    "spotify":    "Spotify",
    "whatsapp":   "WhatsApp",
    "instagram":  "Instagram",
    "linkedin":   "LinkedIn",
    "twitter":    "Twitter",
    "youtube":    "YouTube",
    "tiktok":     "TikTok",
    # Automatización
    "n8n":        "n8n",   # se escribe en minúsculas
    "zapier":     "Zapier",
    "make":       "Make",
}

_WORD_BOUNDARY = r"(?<![A-Za-záéíóúñ]){}(?![A-Za-záéíóúñ])"

# Pre-compilar regexes de siglas y nombres propios (evita recompilación en cada llamada)
_ACRONYM_RES: list[tuple[re.Pattern, str]] = [
    (re.compile(_WORD_BOUNDARY.format(re.escape(acr)), re.IGNORECASE), acr)
    for acr in _ACRONYMS
]
_PROPER_NAME_RES: list[tuple[re.Pattern, str]] = [
    (re.compile(_WORD_BOUNDARY.format(re.escape(lower)), re.IGNORECASE), correct)
    for lower, correct in _PROPER_NAMES.items()
]

# ── 3. Ordinales para detección de listas ──────────────────────────────────

_ORDINALS = (
    r"primero|segundo|tercero|cuarto|quinto|"
    r"sexto|séptimo|octavo|noveno|décimo|"
    r"primer|tercer|undécimo|duodécimo"
)
_MARKER_RE = re.compile(
    rf"(?<![a-záéíóúñ])(?:(?:el|la|los|las|un|una)\s+)?({_ORDINALS})[\s,.:;-]*",
    re.IGNORECASE,
)


# ── Pipeline ────────────────────────────────────────────────────────────────

def _fix_acronyms(text: str) -> str:
    for pattern, acr in _ACRONYM_RES:
        text = pattern.sub(acr, text)
    return text


def _fix_proper_names(text: str) -> str:
    for pattern, correct in _PROPER_NAME_RES:
        text = pattern.sub(correct, text)
    return text


def _fix_sentences(text: str) -> str:
    """Capitaliza la primera letra de cada oración."""
    if text:
        text = text[0].upper() + text[1:]
    text = re.sub(r"([.!?])\s+([a-záéíóúüñ])", lambda m: m.group(1) + " " + m.group(2).upper(), text)
    return text


def _fix_questions(text: str) -> str:
    """Añade ¿ al inicio de preguntas que terminen en ? sin ¿ de apertura."""
    def _add_opening(m):
        sentence = m.group(0)
        stripped = sentence.lstrip()
        if stripped.startswith("¿"):
            return sentence
        leading = sentence[: len(sentence) - len(stripped)]
        return leading + "¿" + stripped
    return re.sub(r"¿?[^.!?¿¡]*\?", _add_opening, text)


def _format_lists(text: str) -> str:
    """Detecta listas con ordinales y las formatea con guiones."""
    markers = list(_MARKER_RE.finditer(text))
    if len(markers) < 2:
        return text

    preamble = text[: markers[0].start()].strip()

    items = []
    for i, match in enumerate(markers):
        start = match.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        content = text[start:end].strip()
        content = re.sub(r"[\s,;.]*\b(y|e|o|u|pero|aunque|además)\s*$", "", content, flags=re.IGNORECASE).strip()
        content = content.rstrip(".,;").strip()
        if content:
            content = content[0].upper() + content[1:]
            items.append(f"- {content}")

    if not items:
        return text

    parts = ([preamble] if preamble else []) + items
    return "\n".join(parts)


def format_text(text: str) -> str:
    text = _fix_acronyms(text)
    text = _fix_proper_names(text)
    text = _fix_sentences(text)
    text = _fix_questions(text)
    text = _format_lists(text)
    return text
