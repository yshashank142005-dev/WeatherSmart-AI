"""
notifier.py — Real notification dispatcher.

Supports:
  - Email  via Gmail SMTP (smtplib)
  - SMS    via Twilio REST API
  - In-App via an in-memory log (polled by /api/notifications)

Configure in backend/.env:
  EMAIL_SENDER=yourgmail@gmail.com
  EMAIL_PASSWORD=your_app_password          # Gmail App Password (not your login password)
  TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
  TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
  TWILIO_FROM_NUMBER=+1XXXXXXXXXX
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

# ── In-app notification store (last 50 notifications) ────────────────────────
_in_app_log: deque = deque(maxlen=50)


def get_in_app_notifications() -> list:
    """Return all in-app notifications (newest first)."""
    return list(reversed(_in_app_log))


def _push_in_app(alert: dict, city: str):
    """Push a notification to the in-app log."""
    _in_app_log.append({
        "id":        len(_in_app_log),
        "type":      alert.get("type", "ALERT"),
        "severity":  alert.get("severity", "medium"),
        "message":   alert.get("message", ""),
        "action":    alert.get("action", ""),
        "city":      city,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "read":      False,
    })


# ── Email ─────────────────────────────────────────────────────────────────────

def send_email(to_address: str, alerts: list, city: str) -> dict:
    """
    Send an HTML alert email via Gmail SMTP.
    Returns {"success": True/False, "message": str}
    """
    sender   = os.getenv("EMAIL_SENDER", "")
    password = os.getenv("EMAIL_PASSWORD", "")

    if not sender or not password:
        return {"success": False, "message": "Email not configured (EMAIL_SENDER / EMAIL_PASSWORD missing in .env)"}

    try:
        subject = f"🌾 WeatherSmart Alert — {city} ({len(alerts)} alert{'s' if len(alerts)>1 else ''})"

        # Build HTML body
        rows = "".join(
            f"""<tr>
                  <td style="padding:12px;border-bottom:1px solid #2d3748;">
                    <strong>{a['type'].replace('_',' ').title()}</strong><br>
                    <span style="color:#e53e3e;font-weight:600">[{a['severity'].upper()}]</span>
                    {a['message']}<br>
                    <em>Action: {a['action']}</em>
                  </td>
               </tr>"""
            for a in alerts
        )

        html = f"""
        <html><body style="font-family:Arial,sans-serif;background:#0f172a;color:#e2e8f0;padding:24px">
          <h2 style="color:#6366f1">🌾 WeatherSmart AI — Weather Alert</h2>
          <p><strong>City:</strong> {city} &nbsp;|&nbsp; <strong>Alerts:</strong> {len(alerts)}</p>
          <table style="width:100%;border-collapse:collapse;background:#1e293b;border-radius:8px;overflow:hidden">
            {rows}
          </table>
          <p style="color:#94a3b8;font-size:12px;margin-top:24px">
            Sent by WeatherSmart AI &bull; {datetime.now().strftime('%Y-%m-%d %H:%M')}
          </p>
        </body></html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = sender
        msg["To"]      = to_address
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_address, msg.as_string())

        logger.info(f"[Notifier] Email sent to {to_address}")
        return {"success": True, "message": f"Email sent to {to_address}"}

    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Email authentication failed. Check EMAIL_SENDER and EMAIL_PASSWORD in .env (use Gmail App Password)."}
    except Exception as e:
        logger.error(f"[Notifier] Email error: {e}")
        return {"success": False, "message": f"Email error: {str(e)}"}


# ── SMS (Twilio) ──────────────────────────────────────────────────────────────

def send_sms(to_number: str, alerts: list, city: str) -> dict:
    """
    Send SMS via Twilio.
    Returns {"success": True/False, "message": str}
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token  = os.getenv("TWILIO_AUTH_TOKEN",  "")
    from_number = os.getenv("TWILIO_FROM_NUMBER", "")

    if not account_sid or not auth_token or not from_number:
        return {"success": False, "message": "SMS not configured (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM_NUMBER missing in .env)"}

    try:
        from twilio.rest import Client  # lazy import — only fails if not installed
        client = Client(account_sid, auth_token)

        body_lines = [f"🌾 WeatherSmart Alert — {city}"]
        for a in alerts[:3]:  # SMS character limit — max 3 alerts
            body_lines.append(f"[{a['severity'].upper()}] {a['type'].replace('_',' ')}: {a['action']}")
        body_lines.append("— WeatherSmart AI")
        body = "\n".join(body_lines)

        msg = client.messages.create(body=body, from_=from_number, to=to_number)
        logger.info(f"[Notifier] SMS sent to {to_number}, SID: {msg.sid}")
        return {"success": True, "message": f"SMS sent to {to_number}"}

    except ImportError:
        return {"success": False, "message": "Twilio not installed. Run: pip install twilio"}
    except Exception as e:
        logger.error(f"[Notifier] SMS error: {e}")
        return {"success": False, "message": f"SMS error: {str(e)}"}


# ── In-App ────────────────────────────────────────────────────────────────────

def send_in_app(alerts: list, city: str) -> dict:
    """Push all alerts to the in-app notification store."""
    for alert in alerts:
        _push_in_app(alert, city)
    return {"success": True, "message": f"{len(alerts)} in-app notification(s) pushed"}
