"""compute_chat_metrics — latência mediana + abandono a partir de timestamps. Critério 2 (P3).

Função pura (sem DB, sem LLM). Mensagens são objetos leves com ``.sent`` (True=vendedor)
e ``.sent_at`` (datetime|None), ordenados por ``sequence``.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services.analysis import compute_chat_metrics


@dataclass
class _Msg:
    sent: bool
    sent_at: datetime | None


T0 = datetime(2026, 1, 21, 10, 0, 0)


def _at(seconds: int) -> datetime:
    return T0 + timedelta(seconds=seconds)


def test_empty_conversation():
    m = compute_chat_metrics([])
    assert m.median_seller_latency_seconds is None
    assert m.median_lead_latency_seconds is None
    assert m.first_response_latency_seconds is None
    assert m.last_message_sent is None
    assert m.is_abandoned is False


def test_single_message():
    m = compute_chat_metrics([_Msg(sent=False, sent_at=T0)])
    assert m.median_seller_latency_seconds is None
    assert m.median_lead_latency_seconds is None
    assert m.first_response_latency_seconds is None
    assert m.last_message_sent is False
    assert m.is_abandoned is False


def test_latencies_and_first_response():
    # lead@0, vendedor@30 (seller gap 30), lead@90 (lead gap 60),
    # vendedor@120 (seller gap 30), lead@320 (lead gap 200)
    msgs = [
        _Msg(sent=False, sent_at=_at(0)),
        _Msg(sent=True, sent_at=_at(30)),
        _Msg(sent=False, sent_at=_at(90)),
        _Msg(sent=True, sent_at=_at(120)),
        _Msg(sent=False, sent_at=_at(320)),
    ]
    m = compute_chat_metrics(msgs)
    # Seller gaps: [30, 30] → mediana 30. Lead gaps: [60, 200] → mediana 130.
    assert m.median_seller_latency_seconds == 30
    assert m.median_lead_latency_seconds == 130
    # Primeira resposta do vendedor (lead→vendedor) = 30s.
    assert m.first_response_latency_seconds == 30
    # Última msg é do lead → não abandonado.
    assert m.last_message_sent is False
    assert m.is_abandoned is False


def test_abandoned_when_seller_last():
    # Termina com o vendedor sem resposta do lead → abandonado.
    msgs = [
        _Msg(sent=False, sent_at=_at(0)),
        _Msg(sent=True, sent_at=_at(60)),
    ]
    m = compute_chat_metrics(msgs)
    assert m.last_message_sent is True
    assert m.is_abandoned is True
    assert m.first_response_latency_seconds == 60
    assert m.median_seller_latency_seconds == 60
    assert m.median_lead_latency_seconds is None


def test_skips_pairs_with_missing_timestamp():
    # all_chats.json import: sem timestamps. Pares sem sent_at são ignorados.
    msgs = [
        _Msg(sent=False, sent_at=None),
        _Msg(sent=True, sent_at=None),
        _Msg(sent=False, sent_at=_at(0)),
        _Msg(sent=True, sent_at=_at(45)),  # único par computável: seller gap 45
    ]
    m = compute_chat_metrics(msgs)
    assert m.median_seller_latency_seconds == 45
    assert m.first_response_latency_seconds == 45
    assert m.median_lead_latency_seconds is None
    # Última msg do vendedor → abandonado (independe de timestamp).
    assert m.last_message_sent is True
    assert m.is_abandoned is True


def test_median_even_count():
    # Quatro gaps de vendedor: [10, 20, 30, 40] → mediana int((20+30)/2)=25.
    msgs = [
        _Msg(sent=False, sent_at=_at(0)),
        _Msg(sent=True, sent_at=_at(10)),
        _Msg(sent=False, sent_at=_at(100)),
        _Msg(sent=True, sent_at=_at(120)),
        _Msg(sent=False, sent_at=_at(200)),
        _Msg(sent=True, sent_at=_at(230)),
        _Msg(sent=False, sent_at=_at(300)),
        _Msg(sent=True, sent_at=_at(340)),
    ]
    m = compute_chat_metrics(msgs)
    assert m.median_seller_latency_seconds == 25
