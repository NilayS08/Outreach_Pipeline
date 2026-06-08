"""
Stage 2 — Find Decision-Makers (Prospeo /search-person)

Input  : list of company domains from Stage 1
Output : list of C-suite / VP contacts with LinkedIn URLs

Prospeo docs : https://prospeo.io/api-docs/search-person
Auth         : X-KEY header
Endpoint     : POST https://api.prospeo.io/search-person

NOTE: /search-person returns profile data but does NOT include emails.
      Emails are resolved separately in Stage 3 via /enrich-person.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

PROSPEO_API_KEY = os.getenv("PROSPEO_API_KEY")
BASE_URL = "https://api.prospeo.io"

# Prospeo's rate limit is 150 req/min — 0.5s delay keeps us well under
RATE_LIMIT_DELAY_SECONDS = 0.5


def find_decision_makers(companies: list[dict]) -> list[dict]:
    """
    Takes a list of company dicts (each with 'domain' and 'name').
    Returns a flat list of C-suite / VP contacts with LinkedIn URLs.

    Each returned dict has:
        - domain        : str  (e.g. "acme.com")
        - company_name  : str
        - first_name    : str
        - last_name     : str
        - full_name     : str
        - title         : str
        - linkedin_url  : str  (needed by Stage 3 to resolve the email)

    Companies with no contacts found are skipped — not a crash.
    """
    if not PROSPEO_API_KEY:
        raise EnvironmentError("PROSPEO_API_KEY is not set in your .env file.")

    headers = {
        "X-KEY": PROSPEO_API_KEY,
        "Content-Type": "application/json",
    }

    all_contacts = []

    for company in companies:
        domain = company["domain"]
        company_name = company.get("name", "Unknown")

        print(f"[Stage 2] Searching decision-makers at: {domain}")

        try:
            response = requests.post(
                f"{BASE_URL}/search-person",
                headers=headers,
                json={
                    "page": 1,
                    "filters": {
                        "company": {
                            "websites": {
                                "include": [domain],
                            },
                        },
                        "person_seniority": {
                            "include": ["C-Suite", "Vice President"],
                        },
                    },
                },
                timeout=30,
            )

            if response.status_code == 429:
                print(f"[Stage 2] Rate limited — waiting 10s before continuing.")
                time.sleep(10)
                continue  # skip this company, don't crash the whole run

            if response.status_code != 200:
                print(
                    f"[Stage 2] Skipping {domain} — "
                    f"API error {response.status_code}: {response.text}"
                )
                continue

            data = response.json()

            # Prospeo returns: { "error": false, "person_list": [...] }
            if data.get("error"):
                print(f"[Stage 2] Prospeo error for {domain}: {data} — skipping.")
                continue

            results = data.get("results", [])

            for result in results:
                person = result.get("person", {})
                company_info = result.get("company", {})

                linkedin_url = person.get("linkedin_url", "").strip()
                if not linkedin_url:
                    continue  # Stage 3 needs the LinkedIn URL — skip if missing

                current_job_title = person.get("current_job_title", "")
                if not current_job_title:
                    current_job_title = person.get("headline", "")

                all_contacts.append({
                    "domain": domain,
                    "company_name": company_info.get("name", company_name),
                    "company_website": company_info.get("website", company_info.get("domain", domain)),
                    "first_name": person.get("first_name", ""),
                    "last_name": person.get("last_name", ""),
                    "full_name": person.get("full_name", ""),
                    "person_id": person.get("person_id", ""),
                    "title": current_job_title,
                    "linkedin_url": linkedin_url,
                })

        except requests.exceptions.RequestException as e:
            print(f"[Stage 2] Network error for {domain}: {e} — skipping.")

        time.sleep(RATE_LIMIT_DELAY_SECONDS)

    print(f"[Stage 2] Found {len(all_contacts)} decision-makers across {len(companies)} companies.")
    return all_contacts

