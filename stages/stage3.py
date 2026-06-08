"""
Stage 3 — Resolve Verified Work Emails (Prospeo /enrich-person)

Input  : list of contacts with LinkedIn URLs from Stage 2
Output : same contacts, now with a verified work email added
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

PROSPEO_API_KEY = os.getenv("PROSPEO_API_KEY")
BASE_URL = "https://api.prospeo.io"

RATE_LIMIT_DELAY_SECONDS = 0.5


def resolve_emails(contacts: list[dict]) -> list[dict]:
    if not PROSPEO_API_KEY:
        raise EnvironmentError("PROSPEO_API_KEY is not set in your .env file.")

    headers = {
        "X-KEY": PROSPEO_API_KEY,
        "Content-Type": "application/json",
    }

    # De-duplicate by LinkedIn URL before hitting the API.
    # No point paying for the same enrichment twice.
    seen = set()
    unique_contacts = []
    for contact in contacts:
        url = contact["linkedin_url"]
        if url not in seen:
            seen.add(url)
            unique_contacts.append(contact)

    duplicates_removed = len(contacts) - len(unique_contacts)
    print(
        f"[Stage 3] Resolving emails for {len(unique_contacts)} contacts "
        f"({duplicates_removed} duplicates removed)."
    )

    resolved = []

    for contact in unique_contacts:
        linkedin_url = contact["linkedin_url"]
        print(f"[Stage 3] Enriching: {contact.get('full_name', linkedin_url)}")

        person_id = contact.get("person_id", "").strip()
        company_website = contact.get("company_website", contact.get("domain", "")).strip()
        company_name = contact.get("company_name", "").strip()

        try:
            data = {
                "linkedin_url": linkedin_url,
                # Prospeo recommends person_id when enriching from search results.
                # Keep the other known datapoints as fallbacks for match accuracy.
                "first_name": contact.get("first_name", ""),
                "last_name": contact.get("last_name", ""),
                "company_name": company_name,
                "company_website": company_website,
            }

            if person_id:
                data = {"person_id": person_id, **data}

            response = requests.post(
                f"{BASE_URL}/enrich-person",
                headers=headers,
                json={
                    # only_verified_email=true means Prospeo will NOT charge a
                    # credit and will NOT return a result unless the email is
                    # verified — exactly what we want before sending outreach.
                    "only_verified_email": True,
                    "data": data,
                },
                timeout=30,
            )

            if response.status_code == 429:
                print("[Stage 3] Rate limited — waiting 10s before continuing.")
                time.sleep(10)
                continue

            if response.status_code != 200:
                print(
                    f"[Stage 3] Skipping {linkedin_url} — "
                    f"API error {response.status_code}: {response.text}"
                )
                continue

            data = response.json()

            if data.get("error"):
                print(f"[Stage 3] No verified email for {linkedin_url} — skipping.")
                continue

            # Prospeo response shape:
            # { "error": false, "person": { "email": { "email": "jane@acme.com", ... }, ... } }
            person = data.get("person", {})
            email_obj = person.get("email", {})
            email = email_obj.get("email", "").strip()

            if not email:
                print(f"[Stage 3] No email returned for {linkedin_url} — skipping.")
                continue

            print(f"[Stage 3] ✓ Resolved: {email}")
            resolved.append({**contact, "email": email})

        except requests.exceptions.RequestException as e:
            print(f"[Stage 3] Network error for {linkedin_url}: {e} — skipping.")

        time.sleep(RATE_LIMIT_DELAY_SECONDS)

    print(
        f"[Stage 3] Resolved {len(resolved)} verified emails "
        f"out of {len(unique_contacts)} contacts."
    )
    return resolved

