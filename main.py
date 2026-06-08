
import sys
from stages.stage1_ocean import find_lookalike_companies
from stages.stage2_prospeo import find_decision_makers
from stages.stage3_eazyreach import resolve_emails
from stages.stage4_brevo import send_outreach_emails
from stages.stage4_brevo import send_outreach_emails, build_email_subject, build_email_body


def print_banner(stage_number: int, title: str):
    print(f"\n{'='*55}")
    print(f"  STAGE {stage_number}: {title}")
    print(f"{'='*55}")


def safety_checkpoint(contacts: list[dict]) -> bool:
    print(f"\n{'='*55}")
    print(" SAFETY CHECKPOINT — Review before sending")
    print(f"{'='*55}")
    print(f"\nAbout to send {len(contacts)} emails:\n")

    for i, contact in enumerate(contacts, start=1):
        name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        print(f"  {i:>2}. {name} ({contact.get('title', 'N/A')})"
              f" at {contact.get('company_name', 'N/A')}"
              f" → {contact.get('email', 'N/A')}")
    
    print("\nEmail preview:\n")
    for i, contact in enumerate(contacts, start=1):
        print(f"  {i:>2}. Subject: {build_email_subject(contact)}")
        print("     Body:")
        print(build_email_body(contact).strip())
        print()

    print()
    answer = input("Send these emails? Type 'yes' to confirm, anything else to abort: ").strip().lower()
    return answer == "yes"



def run_pipeline(seed_domain: str):
    print(f"\nStarting pipeline for seed domain: {seed_domain}\n")

    # ── Stage 1: Find lookalike companies ───────────────────────────────────
    print_banner(1, "Find Lookalike Companies (Ocean.io)")
    companies = find_lookalike_companies(seed_domain)

    if not companies:
        print("No lookalike companies found. Exiting.")
        return

    # ── Stage 2: Find decision-makers ───────────────────────────────────────
    print_banner(2, "Find Decision-Makers (Prospeo)")
    contacts = find_decision_makers(companies)

    if not contacts:
        print("No decision-makers found. Exiting.")
        return

    # ── Stage 3: Resolve verified work emails ───────────────────────────────
    print_banner(3, "Resolve Work Emails (Eazyreach)")
    resolved_contacts = resolve_emails(contacts)

    if not resolved_contacts:
        print("No verified emails resolved. Exiting.")
        return

    # ── Safety Checkpoint ───────────────────────────────────────────────────
    confirmed = safety_checkpoint(resolved_contacts)
    if not confirmed:
        print("\nAborted by user. No emails were sent.")
        return

    # ── Stage 4: Send personalized outreach ─────────────────────────────────
    print_banner(4, "Send Personalized Outreach (Brevo)")
    result = send_outreach_emails(resolved_contacts)

    # ── Final summary ───────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print("  PIPELINE COMPLETE")
    print(f"{'='*55}")
    print(f"  Seed domain   : {seed_domain}")
    print(f"  Companies found : {len(companies)}")
    print(f"  Contacts found  : {len(contacts)}")
    print(f"  Emails resolved : {len(resolved_contacts)}")
    print(f"  Emails sent     : {result['sent']}")
    print(f"  Emails failed   : {result['failed']}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <seed_domain>")
        print("Example: python main.py stripe.com")
        sys.exit(1)

    seed = sys.argv[1].strip().lower()

    # Strip any http:// or https:// if the user accidentally included it
    seed = seed.replace("https://", "").replace("http://", "").rstrip("/")

    run_pipeline(seed)
