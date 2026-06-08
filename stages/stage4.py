"""
Stage 4 — Send Personalized Outreach (Brevo)

Input  : list of contacts with verified emails from Stage 3
Output : emails sent via Brevo transactional API
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")
SENDER_NAME = os.getenv("BREVO_SENDER_NAME")

BASE_URL = "https://api.brevo.com/v3"

RATE_LIMIT_DELAY_SECONDS = 0.5  # Brevo is generous but still be polite


def build_email_subject(contact: dict) -> str:
    first_name = contact.get("first_name", "there")
    company = contact.get("company_name", "your company")
    return f"Quick question for {first_name} at {company}"


def build_email_body(contact: dict) -> str:
    first_name = contact.get("first_name", "there")
    company = contact.get("company_name", "your company")
    title = contact.get("title", "leader")

    return f"""
    <p>Hi {first_name},</p>

    <p>
        I came across {company} and noticed that as {title}, you're likely thinking
        about how to scale your outreach without scaling your team.
    </p>

    <p>
        We build fully automated cold-outreach pipelines — one domain in, qualified
        leads and sent emails out, zero humans in the loop. The kind of system that
        finds companies like yours, locates the right person, and sends a tailored
        email — all on its own.
    </p>

    <p>
        Would you be open to a 15-minute call to see if this fits what you're working on?
    </p>

    <p>
        Best,<br>
        {SENDER_NAME}
    </p>
    """


def send_outreach_emails(contacts: list[dict]) -> dict:
    if not BREVO_API_KEY:
        raise EnvironmentError("BREVO_API_KEY is not set in your .env file.")
    if not SENDER_EMAIL:
        raise EnvironmentError("BREVO_SENDER_EMAIL is not set in your .env file.")

    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
    }

    summary = {"sent": 0, "failed": 0, "details": []}

    for contact in contacts:
        email = contact["email"]
        first_name = contact.get("first_name", "")
        last_name = contact.get("last_name", "")

        payload = {
            "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
            "to": [{"email": email, "name": f"{first_name} {last_name}".strip()}],
            "subject": build_email_subject(contact),
            "htmlContent": build_email_body(contact),
        }

        print(f"[Stage 4] Sending email to: {email}")

        try:
            response = requests.post(
                f"{BASE_URL}/smtp/email",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code in (200, 201):
                print(f"[Stage 4] ✓ Sent to {email}")
                summary["sent"] += 1
                summary["details"].append({"email": email, "status": "sent", "reason": ""})
            else:
                reason = response.text
                print(f"[Stage 4] ✗ Failed for {email} — {response.status_code}: {reason}")
                summary["failed"] += 1
                summary["details"].append({"email": email, "status": "failed", "reason": reason})

        except requests.exceptions.RequestException as e:
            print(f"[Stage 4] Network error for {email}: {e}")
            summary["failed"] += 1
            summary["details"].append({"email": email, "status": "failed", "reason": str(e)})

        time.sleep(RATE_LIMIT_DELAY_SECONDS)

    print(f"\n[Stage 4] Done — {summary['sent']} sent, {summary['failed']} failed.")
    return summary

