from unittest.mock import patch

from agent.composition import (
    compose_critical_alert,
    compose_daily_digest,
    _fallback_template,
)
from agent.models import NormalizedSKU


def _sample_sku(sku="SKU-A", urgency="CRITICAL"):
    return NormalizedSKU(
        sku=sku,
        product_name="Test Product",
        current_stock=5,
        avg_daily_sales=2.0,
        days_of_supply=2.5,
        lead_time_days=7,
        reorder_point=21.0,
        suggested_reorder_qty=21,
        urgency=urgency,
    )


def test_fallback_template_contains_sku():
    out = _fallback_template([_sample_sku()])
    assert "SKU-A" in out
    assert "5 in stock" in out
    assert "CRITICAL" in out


def test_compose_critical_uses_groq_when_available():
    with patch("agent.composition._call_groq", return_value="LLM wrote this") as m:
        out = compose_critical_alert([_sample_sku()])
        assert out == "LLM wrote this"
        m.assert_called_once()


def test_compose_critical_falls_back_on_error():
    with patch("agent.composition._call_groq", side_effect=RuntimeError("boom")):
        out = compose_critical_alert([_sample_sku()])
        assert "SKU-A" in out
        assert "CRITICAL" in out


def test_compose_digest_uses_groq_when_available():
    with patch("agent.composition._call_groq", return_value="Digest body"):
        out = compose_daily_digest([_sample_sku(urgency="HIGH")])
        assert out == "Digest body"


def test_compose_empty_returns_empty():
    assert compose_critical_alert([]) == ""
    assert compose_daily_digest([]) == ""