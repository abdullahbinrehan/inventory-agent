"""
Composition layer.

Turns structured SKU data into a human-readable alert message using an LLM.
Fallback chain: Groq -> OpenRouter -> plain template.
"""

import logging

from groq import Groq

from agent import config
from agent.models import NormalizedSKU

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _format_skus_for_prompt(skus: list[NormalizedSKU]) -> str:
    lines = []
    for s in skus:
        lines.append(
            f"- {s.product_name} (SKU: {s.sku}) | "
            f"stock: {s.current_stock} | "
            f"avg daily sales: {s.avg_daily_sales} | "
            f"days of supply: {s.days_of_supply} | "
            f"suggested reorder: {s.suggested_reorder_qty} units | "
            f"urgency: {s.urgency}"
        )
    return "\n".join(lines)


def _build_prompt(skus: list[NormalizedSKU], digest: bool = False) -> str:
    header = (
        "You are an inventory assistant writing to a busy store owner. "
        "Write a concise, clear email."
    )
    if digest:
        header += " This is a daily digest — group items by urgency, keep it scannable."
    else:
        header += " This is an URGENT alert — lead with the most critical item."

    body = (
        f"\n\nInventory status:\n{_format_skus_for_prompt(skus)}\n\n"
        "Requirements:\n"
        "- Use short paragraphs or bullet points.\n"
        "- For each item include: product name, current stock, days of supply, "
        "and suggested reorder quantity.\n"
        "- Do NOT invent data. Use only what is provided.\n"
        "- Do NOT add a subject line — just the body.\n"
        "- Keep it under 250 words."
    )
    return header + body


# ---------------------------------------------------------------------------
# LLM callers
# ---------------------------------------------------------------------------

def _call_groq(prompt: str) -> str:
    client = Groq(api_key=config.GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()


def _fallback_template(skus: list[NormalizedSKU]) -> str:
    """Plain-text fallback if the LLM is unavailable."""
    lines = ["Inventory alert:\n"]
    for s in skus:
        lines.append(
            f"- {s.product_name} ({s.sku}): {s.current_stock} in stock, "
            f"{s.days_of_supply} days of supply. "
            f"Suggested reorder: {s.suggested_reorder_qty} units. "
            f"[{s.urgency}]"
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