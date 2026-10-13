"""
Error handling utilities.

Sends error notifications to Discord #logs and email when the pipeline crashes.
"""

import logging
import platform
import traceback
from datetime import datetime, timezone

from agent import config
from agent.discord_webhook import send_log
from agent.emailer import send_email

logger = logging.getLogger(__name__)


def send_error_alert(exception: BaseException) -> None:
    """
    Send a formatted error report to Discord #logs and email.
    Never raises — if notification itself fails, we log and move on.
    """
    tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Truncate to avoid Discord/email size limits
    tb_short = tb[-3500:] if len(tb) > 3500 else tb

    # --- Discord ---
    discord_msg = (
        f"❌ **Pipeline crashed** at {ts}\n"
        f"**Type:** `{type(exception).__name__}`\n"
        f"**Message:** `{str(exception)[:500]}`\n"
        f"**Platform:** {platform.system()} {platform.release()}\n"
        f"**Python:** {platform.python_version()}\n"
        f"```\n{tb_short}\n```"
    )
    try:
        send_log(discord_msg)
    except Exception as e:
        logger.error("Failed to send error alert to Discord: %s", e)

    # --- Email ---
    try:
        plain = (
            f"Pipeline crashed at {ts}\n\n"
            f"Type: {type(exception).__name__}\n"
            f"Message: {exception}\n\n"
            f"Full traceback:\n{tb}"
        )
        html = f"""
        <html><body style="font-family: -apple-system, sans-serif; padding: 20px; background: #f3f4f6;">
          <div style="max-width: 700px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <div style="background: linear-gradient(135deg, #ef4444, #991b1b); color: #fff; padding: 24px 28px;">
              <h1 style="margin: 0; font-size: 20px;">❌ Pipeline Crashed</h1>
              <p style="margin: 6px 0 0; opacity: 0.9; font-size: 13px;">{ts}</p>
            </div>
            <div style="padding: 24px 28px;">
              <p><strong>Type:</strong> {type(exception).__name__}</p>
              <p><strong>Message:</strong> {exception}</p>
              <p><strong>Platform:</strong> {platform.system()} {platform.release()}</p>
              <p><strong>Python:</strong> {platform.python_version()}</p>
              <h3 style="margin-top: 24px; color: #374151;">Traceback</h3>
              <pre style="background: #1f2937; color: #f9fafb; padding: 16px; border-radius: 8px; font-size: 12px; overflow-x: auto; white-space: pre-wrap;">{tb}</pre>
            </div>
          </div>
        </body></html>
        """
        send_email(
            subject=f"❌ inventory-agent crashed: {type(exception).__name__}",
            plain_body=plain,
            html_body=html,
        )
    except Exception as e:
        logger.error("Failed to send error alert via email: %s", e)