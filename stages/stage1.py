"""
Stage 1 — Find Lookalike Companies (Ocean.io)

Input  : seed domain (e.g. "stripe.com")
Output : list of similar company domains
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

OCEAN_API_KEY = os.getenv("OCEAN_API_KEY")
BASE_URL = "https://api.ocean.io/v3"


def find_lookalike_companies(seed_domain: str, limit: int = 10) -> list[dict]:
    if not OCEAN_API_KEY:
        raise EnvironmentError("OCEAN_API_KEY is not set in your .env file.")

    headers = {
        "X-Api-Token": OCEAN_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "size": limit,
        "companiesFilters": {
            "lookalikeDomains": [seed_domain],
        },
    }

    print(f"[Stage 1] Searching for companies similar to: {seed_domain}")

    response = requests.post(
        f"{BASE_URL}/search/companies",
        headers=headers,
        json=payload,
        timeout=30,
    )

    # surface the error clearly so you know exactly what went wrong
    if response.status_code != 200:
        raise Exception(
            f"[Stage 1] Ocean.io API error {response.status_code}: {response.text}"
        )

    data = response.json()

    companies = data.get("companies", [])

    results = []
    for company in companies:
        company_data = company.get("company", company)
        domain = company_data.get("domain", "").strip()
        name = company_data.get("name", "Unknown")
        if domain:  # skip any entry with no domain
            results.append({"domain": domain, "name": name})

    print(f"[Stage 1] Found {len(results)} lookalike companies.")
    return results

