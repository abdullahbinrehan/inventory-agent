"""
Composition layer.

Turns structured SKU data into a human-readable alert message using an LLM.
Fallback chain: Groq -> plain template.
"""

import logging

from groq import Groq

from agent import config
from agent.models import NormalizedSKU

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _format_skus_for_prompt(skus: list[NormalizedSKU]) -> str:
    lines = []
    for s in skus:
        # Human-readable trend description
        if s.sales_trend_pct > 0.15:
            trend = f"growing (+{int(s.sales_trend_pct * 100)}% WoW)"
        elif s.sales_trend_pct < -0.15:
            trend = f"declining ({int(s.sales_trend_pct * 100)}% WoW)"
        else:
            trend = "steady"

        # Human-readable spike description
        if s.spike_ratio >= 2.0:
            spike = f"spiking TODAY ({s.spike_ratio}x normal)"
        else:
            spike = "no spike"

        lines.append(
            f"- {s.product_name} (SKU: {s.sku})\n"
            f"    stock: {s.current_stock} | "
            f"avg daily sales: {s.avg_daily_sales} | "
            f"days of supply: {s.days_of_supply} | "
            f"reorder: {s.suggested_reorder_qty} units\n"
            f"    urgency: {s.urgency} | trend: {trend} | {spike}"
        )
    return "\n".join(lines)


def _build_prompt(skus: list[NormalizedSKU], digest: bool = False) -> str:
    tone = (
        "URGENT — the owner needs to act today."
        if not digest
        else "Informational — the owner should keep these on their radar."
    )

    return f"""You are an inventory analyst writing to a busy store owner.

Situation: {tone}

Current inventory snapshot:
{_format_skus_for_prompt(skus)}

Write a concise email body that:

1. OPENS with a one-sentence summary of the overall situation
   (e.g. "3 shirts are critically low and 2 accessories are trending down.")

2. For each SKU, briefly explains WHY it is low, drawing on the trend and spike
   data. Do NOT just restate the numbers — interpret them.
   Example: "Black T-Shirt is the most urgent — sales spiked 3x today and you
   have under 3 days of cover."

3. Ends with a short recommended action.

Constraints:
- Do NOT invent data. Only use what's provided.
- Do NOT include a subject line — just the body.
- Keep it under 220 words.
- Use short paragraphs or bullet points.
- Be direct and actionable.
"""


# ---------------------------------------------------------------------------
# LLM callers
# ---------------------------------------------------------------------------

def _call_groq(prompt: str) -> str:
    client = Groq(api_key=config.GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=700,
    )
    return response.choices[0].message.content.strip()


def _fallback_template(skus: list[NormalizedSKU]) -> str:
    """Plain-text fallback if the LLM is unavailable."""
    lines = ["Inventory alert:\n"]
    for s in skus:
        reason_bits = []
        if s.sales_trend_pct > 0.15:
            reason_bits.append(f"sales up {int(s.sales_trend_pct * 100)}% WoW")
        elif s.sales_trend_pct < -0.15:
            reason_bits.append(f"sales down {int(abs(s.sales_trend_pct) * 100)}% WoW")
        if s.spike_ratio >= 2.0:
            reason_bits.append(f"spiking {s.spike_ratio}x today")
        reason = f" ({', '.join(reason_bits)})" if reason_bits else ""

        lines.append(
            f"- {s.product_name} ({s.sku}): "
            f"{s.current_stock} in stock, {s.days_of_supply} days of supply. "
            f"Reorder {s.suggested_reorder_qty} units. [{s.urgency}]{reason}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public composers
# ---------------------------------------------------------------------------

def compose_critical_alert(skus: list[NormalizedSKU]) -> str:
    """Compose an urgent alert for CRITICAL SKUs."""
    if not skus:
        return ""
    prompt = _build_prompt(skus, digest=False)
    try:
        return _call_groq(prompt)
    except Exception as e:
        logger.warning("Groq failed, using template: %s", e)
        return _fallback_template(skus)


def compose_daily_digest(skus: list[NormalizedSKU]) -> str:
    """Compose a daily digest for HIGH + NORMAL SKUs."""
    if not skus:
        return ""
    prompt = _build_prompt(skus, digest=True)
    try:
        return _call_groq(prompt)
    except Exception as e:
        logger.warning("Groq failed, using template: %s", e)
        return _fallback_template(skus)