"""Parser de exportações do WhatsApp (porte de ``wpp2db.py`` — só o parsing de texto).

Descartados do original: SQLite, Whisper/OpenAI, FFmpeg, UUID e extração de mídia por
posição. Mantido: split por fronteira de timestamp (trata multi-linha), papel do
remetente (``~`` ⇒ lead), filtro de mensagens de sistema PT, limpeza de U+200E e
mapeamento de mídia para placeholder PT.

Formato de linha: ``[DD/MM/YYYY, HH:MM:SS] Remetente: corpo`` (``~Remetente`` ⇒ lead).
"""

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

U200E = "‎"

# Fronteira de mensagem: cada timestamp inicia uma nova mensagem.
_TS_BOUNDARY = re.compile(r"\[(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})\]")
# Parse por mensagem: timestamp, remetente (até o primeiro ':'), corpo (DOTALL p/ multi-linha).
_MSG = re.compile(
    r"\[(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})\] ([^:]+): (.+)", re.DOTALL
)
_TS_FMT = "%d/%m/%Y, %H:%M:%S"

# Mensagens de sistema PT a filtrar (match por substring).
_SYSTEM_MESSAGES = (
    "As mensagens e ligações são protegidas com a criptografia de ponta a ponta",
    "Esta conversa foi iniciada em um anúncio no Facebook",
)

# Marcadores de mídia oculta/omitida (sem nome de arquivo).
_HIDDEN_MEDIA = ("<mídia oculta>", "mídia ocultada", "media omitted", "<arquivo de mídia oculto>")

_MEDIA_BY_EXT = {
    ".opus": "[áudio]", ".mp3": "[áudio]", ".m4a": "[áudio]", ".ogg": "[áudio]",
    ".jpg": "[imagem]", ".jpeg": "[imagem]", ".png": "[imagem]", ".gif": "[imagem]",
    ".webp": "[imagem]",
    ".pdf": "[documento]", ".doc": "[documento]", ".docx": "[documento]",
}
_MEDIA_FALLBACK = "[mídia]"

# Captura o nome do arquivo dentro de <anexado: nome.ext>.
_ANEXADO = re.compile(r"<anexado:\s*([^>]+)>", re.IGNORECASE)


class WhatsAppParseError(Exception):
    """Erro base de parsing de exportação do WhatsApp."""


class EmptyChatError(WhatsAppParseError):
    """O conteúdo está vazio ou só tem espaços."""

    def __init__(self) -> None:
        super().__init__("O arquivo de conversa está vazio.")


class NotWhatsAppExportError(WhatsAppParseError):
    """Nenhum timestamp no formato do WhatsApp foi encontrado."""

    def __init__(self) -> None:
        super().__init__(
            "Arquivo não reconhecido como exportação do WhatsApp "
            "(nenhuma mensagem no formato [DD/MM/AAAA, HH:MM:SS])."
        )


@dataclass
class ParsedMessage:
    text: str
    sent: bool  # True ⇔ vendedor; False ⇔ lead.
    sent_at: datetime
    sequence: int


def _clean_u200e(text: str) -> str:
    """Remove U+200E das bordas das mensagens, preservando o que estiver no meio do corpo."""
    cleaned = re.sub(r"‎\s*(?=\[\d{2}/\d{2}/\d{4})", "", text)
    cleaned = re.sub(r"‎\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"‎\s*\n(?=\[\d{2}/\d{2}/\d{4})", "\n", cleaned)
    return cleaned


def _is_system_message(body: str) -> bool:
    return any(sysmsg in body for sysmsg in _SYSTEM_MESSAGES)


def _map_media(body: str) -> str | None:
    """Se o corpo for mídia, devolve o placeholder PT; senão None (texto normal)."""
    low = body.lower()
    if any(marker in low for marker in _HIDDEN_MEDIA):
        return _MEDIA_FALLBACK
    m = _ANEXADO.search(body)
    if m:
        filename = m.group(1).strip()
        dot = filename.rfind(".")
        ext = filename[dot:].lower() if dot != -1 else ""
        return _MEDIA_BY_EXT.get(ext, _MEDIA_FALLBACK)
    return None


def _split_messages(text: str) -> list[str]:
    """Fatia o texto em blocos por fronteira de timestamp (multi-linha vira um bloco só)."""
    matches = list(_TS_BOUNDARY.finditer(text))
    blocks = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        if block:
            blocks.append(block)
    return blocks


def parse_chat(text: str) -> list[ParsedMessage]:
    """Faz o parse do ``_chat.txt`` em ``ParsedMessage``s, filtrando sistema/vazias.

    Levanta ``EmptyChatError`` se o conteúdo for vazio e ``NotWhatsAppExportError``
    se não houver nenhum timestamp no formato do WhatsApp. ``sequence`` é 0-based e
    contígua, atribuída após a filtragem.
    """
    if not text or not text.strip():
        raise EmptyChatError()

    cleaned = _clean_u200e(text)
    if not _TS_BOUNDARY.search(cleaned):
        raise NotWhatsAppExportError()

    parsed: list[ParsedMessage] = []
    for block in _split_messages(cleaned):
        block = block.replace(U200E, "").strip()
        m = _MSG.match(block)
        if not m:
            continue
        ts_str, sender, body = m.groups()
        body = body.strip()
        if not body or _is_system_message(body):
            continue

        sender = sender.strip()
        sent = not sender.startswith("~")  # vendedor não tem ~

        placeholder = _map_media(body)
        if placeholder is not None:
            body = placeholder

        try:
            sent_at = datetime.strptime(ts_str, _TS_FMT)
        except ValueError:
            continue

        parsed.append(
            ParsedMessage(text=body, sent=sent, sent_at=sent_at, sequence=len(parsed))
        )

    return parsed


def infer_lead_name(text: str) -> str | None:
    """Nome do lead = remetente ``~`` mais frequente (sem o til). None se não houver."""
    senders: Counter[str] = Counter()
    for m in _MSG.finditer(text):
        sender = m.group(2).strip()
        if sender.startswith("~"):
            senders[sender[1:].strip()] += 1
    if not senders:
        return None
    return senders.most_common(1)[0][0]


def phone_from_filename(filename: str) -> str | None:
    """``WhatsApp Chat - <phone>.zip``/``.txt`` → ``<phone>``; senão None."""
    base = filename.rsplit("/", 1)[-1]
    m = re.match(r"WhatsApp Chat - (.+)\.(zip|txt)$", base, re.IGNORECASE)
    return m.group(1).strip() if m else None
