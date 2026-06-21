"""Parser de WhatsApp (porte de wpp2db.py — só parsing). Critérios 2–6 (P2).

Cobre: multi-linha, papel do remetente (~ → lead), filtro de sistema/vazias,
placeholders de mídia, erros tipados, e os helpers phone_from_filename / infer_lead_name.
"""

import pytest

from app.services.whatsapp_parser import (
    EmptyChatError,
    NotWhatsAppExportError,
    infer_lead_name,
    parse_chat,
    phone_from_filename,
)

E2E_NOTICE = (
    "As mensagens e ligações são protegidas com a criptografia de ponta a ponta. "
    "Somente as pessoas que fazem parte da conversa podem ler, ouvir e compartilhar "
    "esse conteúdo."
)
FB_NOTICE = (
    "Esta conversa foi iniciada em um anúncio no Facebook. O compartilhamento de "
    "dados de atividades relacionadas a clientes está ativado."
)


def test_multiline():
    """Uma mensagem com várias linhas continua sendo uma única ParsedMessage."""
    text = (
        "[20/01/2026, 10:00:00] ~Maria Silva: Olá, gostaria de saber\n"
        "mais sobre o curso\n"
        "de implantodontia\n"
        "[20/01/2026, 10:01:00] MR Digital: Claro! Posso te ajudar.\n"
    )
    parsed = parse_chat(text)
    assert len(parsed) == 2
    assert parsed[0].text == (
        "Olá, gostaria de saber\nmais sobre o curso\nde implantodontia"
    )
    assert parsed[0].sequence == 0
    assert parsed[1].sequence == 1


def test_sender_role():
    """``~Sender`` ⇒ lead (sent=False); sem ``~`` ⇒ vendedor (sent=True)."""
    text = (
        "[20/01/2026, 10:00:00] ~Maria Silva: Oi\n"
        "[20/01/2026, 10:01:00] MR Digital: Olá!\n"
    )
    parsed = parse_chat(text)
    assert parsed[0].sent is False  # lead
    assert parsed[1].sent is True  # vendedor


def test_system_filter():
    """As 2 mensagens de sistema PT e corpos vazios são removidos; sequence fica contígua."""
    text = (
        f"[20/01/2026, 10:00:00] ~Maria Silva: {E2E_NOTICE}\n"
        f"[20/01/2026, 10:00:01] ~Maria Silva: {FB_NOTICE}\n"
        "[20/01/2026, 10:01:00] ~Maria Silva: Primeira real\n"
        "[20/01/2026, 10:02:00] MR Digital: Segunda real\n"
    )
    parsed = parse_chat(text)
    assert [m.text for m in parsed] == ["Primeira real", "Segunda real"]
    assert [m.sequence for m in parsed] == [0, 1]


def test_media_placeholder():
    """Mídia anexada/oculta vira placeholder PT por extensão."""
    text = (
        "[20/01/2026, 10:00:00] ~Maria Silva: <anexado: 00000003-AUDIO-2026.opus>\n"
        "[20/01/2026, 10:01:00] ~Maria Silva: <anexado: foto.jpg>\n"
        "[20/01/2026, 10:02:00] ~Maria Silva: <anexado: contrato.pdf>\n"
        "[20/01/2026, 10:03:00] ~Maria Silva: <Mídia oculta>\n"
    )
    parsed = parse_chat(text)
    assert [m.text for m in parsed] == ["[áudio]", "[imagem]", "[documento]", "[mídia]"]


def test_typed_errors():
    """Vazio → EmptyChatError; prosa sem timestamp → NotWhatsAppExportError."""
    with pytest.raises(EmptyChatError):
        parse_chat("   \n\t  ")
    with pytest.raises(NotWhatsAppExportError):
        parse_chat("Isto é um texto qualquer sem nenhum timestamp do WhatsApp.")


def test_phone_from_filename():
    assert phone_from_filename("WhatsApp Chat - +55 11 99999-0001.zip") == "+55 11 99999-0001"
    assert phone_from_filename("WhatsApp Chat - +55 11 99999-0001.txt") == "+55 11 99999-0001"
    assert phone_from_filename("qualquer_coisa.txt") is None


def test_infer_lead_name():
    """Nome do lead = remetente ``~`` mais frequente (sem o til)."""
    text = (
        "[20/01/2026, 10:00:00] ~Maria Silva: Oi\n"
        "[20/01/2026, 10:01:00] MR Digital: Olá!\n"
        "[20/01/2026, 10:02:00] ~Maria Silva: Tudo bem?\n"
    )
    assert infer_lead_name(text) == "Maria Silva"
    # Sem nenhum remetente ~ → None.
    assert infer_lead_name("[20/01/2026, 10:00:00] MR Digital: Olá!\n") is None
