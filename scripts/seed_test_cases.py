"""
scripts/seed_test_cases.py
==========================
End-to-end test script: Creates 75 realistic dummy cases via the live API,
then verifies AI categorisation, priority assignment, routing to the correct
team, and AI-agent auto-resolution behaviour.

Usage:
    python scripts/seed_test_cases.py

Requirements:
    pip install requests tabulate colorama
"""

import requests
import time
import json
from tabulate import tabulate
from colorama import Fore, Style, init
import sys

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

init(autoreset=True, strip=False)

# --- Config -----------------------------------------------------------------
# Nginx proxy is on port 80; port 3000 is the raw Next.js dev server
BASE_URL   = "http://localhost/api"
ADMIN_CRED = {"email": "admin@csplatform.local", "password": "Admin@123"}
CUST_CRED  = {"email": "customer@csplatform.local", "password": "Admin@123"}

# Teams in DB (from seed.sql)
TEAM_NAMES = {
    "11111111-1111-1111-1111-111111111111": "Tier 1 Support",
    "22222222-2222-2222-2222-222222222222": "Tier 2 Support",
    "33333333-3333-3333-3333-333333333333": "Billing Team",
    "44444444-4444-4444-4444-444444444444": "Management",
    "88888888-8888-8888-8888-888888888888": "AI Agent Queue",
}

AI_AGENT_ID = "99999999-9999-9999-9999-999999999999"

# ─── 75 test cases across all 6 categories ─────────────────────────────────
# Format: (title, message)
TEST_CASES = [
    # ── MORTGAGE (12 cases) ────────────────────────────────────────────────
    ("Mortgage payment not processed",
     "I made my monthly mortgage payment three days ago but it still hasn't been credited to my account. My payment reference is MOR-2024-98211."),
    ("Wrong interest rate applied to my mortgage",
     "My mortgage statement shows an interest rate of 5.9% but my contract clearly states 4.75%. This has been overcharging me for months."),
    ("Mortgage pre-approval taking too long",
     "I applied for mortgage pre-approval 6 weeks ago and have heard nothing. I need to put an offer on a house next week."),
    ("Early repayment charge dispute",
     "I was charged a £3,200 early repayment fee but was never informed this penalty existed. I want a full refund of this charge."),
    ("Property valuation seems too low",
     "The surveyor valued my property at £240,000 which is significantly below the market rate of £290,000. I want to dispute this valuation."),
    ("Mortgage statement shows incorrect balance",
     "My current statement shows an outstanding balance that is £8,500 higher than what I calculated after all my payments. Please audit my account."),
    ("Trouble uploading documents for mortgage application",
     "Your online portal keeps rejecting my PDF documents stating they are too large. I cannot submit my income proof."),
    ("Change of mortgage payment date request",
     "I would like to change my mortgage payment date from the 1st to the 15th of each month to align with my salary payment."),
    ("Mortgage arrears handling complaint",
     "I fell behind on 2 payments due to illness and your collections team has been harassing me daily. I have a repayment plan in place."),
    ("Rate switch mortgage request",
     "My fixed-rate deal expires next month. I would like to switch to the 2-year tracker rate. Please advise on the process."),
    ("Joint mortgage application query",
     "My partner and I are applying for a joint mortgage. We need advice on how income is assessed for a self-employed applicant."),
    ("Help understanding mortgage offer letter",
     "I received my mortgage offer letter but several clauses are unclear to me. Can someone call me to explain the terms?"),

    # ── DEBT COLLECTION (12 cases) ─────────────────────────────────────────
    ("Debt I don't recognise on my credit file",
     "A collections agency is contacting me about a £1,400 debt I have no knowledge of. I have never had an account with this company."),
    ("Harassment by collections team",
     "Your debt collectors have called me 14 times in the past 3 days including on Sundays. This is causing severe anxiety."),
    ("Debt statute barred dispute",
     "I have been contacted about an alleged debt from 2014. This debt is statute barred under UK law and I dispute any liability."),
    ("Incorrect debt amount demanded",
     "The letter I received claims I owe £2,300 but my records show the balance was fully settled in January 2023."),
    ("Debt sold to third party without notice",
     "I received a letter from a different company claiming to own my debt. I was never notified of this sale. Is this legal?"),
    ("Payment arrangement not being honoured",
     "I set up a payment arrangement of £50/month but I am still being charged late fees and receiving threatening letters."),
    ("Dispute collection charge added to balance",
     "An extra £240 collection charge has been added to my debt balance. I was not warned about these additional fees."),
    ("Request for debt validation letter",
     "Please provide written validation of the debt you claim I owe, including the original creditor and account history."),
    ("Collections contact after bankruptcy discharge",
     "I was discharged from bankruptcy 6 months ago. You should not be contacting me about any pre-bankruptcy debts."),
    ("Incorrect account number on collection notice",
     "The account number referenced in your collection notice does not match any account I have ever held with your institution."),
    ("Debt paid but still receiving calls",
     "I paid this debt in full on 15th March. I have the bank transfer confirmation. Please stop all collection activity."),
    ("Threat of legal action seems disproportionate",
     "I owe £180 and you are threatening county court action. Can we discuss an affordable payment plan instead?"),

    # ── CREDIT REPORTING (12 cases) ────────────────────────────────────────
    ("Late payment incorrectly marked on credit report",
     "My credit report shows a late payment in February but my bank records confirm the payment was made on time."),
    ("Account not removed from report after closure",
     "I closed this account 3 years ago but it still appears as 'open' on my credit report, which is affecting my score."),
    ("Credit score dropped unexpectedly",
     "My credit score fell by 120 points this week. I have not applied for any new credit or missed any payments."),
    ("Wrong address listed on credit file",
     "My credit file shows an address where I have never lived. This could be a sign of identity fraud."),
    ("Hard inquiry I did not authorise",
     "There is a hard inquiry on my credit report from a lender I have never approached. Please investigate this."),
    ("Bankruptcy should not appear on report",
     "My bankruptcy was discharged 7 years ago. Under the Fair Credit Reporting Act this must be removed from my report."),
    ("Multiple accounts showing same debt",
     "The same debt appears twice on my credit report under two different collection agency names. This is inflating my debt total."),
    ("Dispute inaccurate loan balance",
     "My student loan balance on my credit file is £4,000 higher than my actual account statement shows."),
    ("Name misspelled on credit report",
     "My surname is spelled incorrectly on my credit file which is causing issues when lenders try to verify my identity."),
    ("Request for credit freeze",
     "I believe I am a victim of identity theft. Please place an immediate credit freeze on my account."),
    ("Negative mark from an account I was not responsible for",
     "My ex-partner had a joint account in my name that I was unaware of. The defaults on this account are affecting my score."),
    ("Credit report does not reflect recent payments",
     "I have made 6 consecutive on-time payments this year but none of these appear on my credit report."),

    # ── BANK ACCOUNT (12 cases) ────────────────────────────────────────────
    ("Unauthorised transaction on my current account",
     "There are two transactions I do not recognise totalling £347.50. One was at a foreign merchant and one online."),
    ("Account locked after too many PIN attempts",
     "I tried my PIN three times at the ATM and my card got locked. I cannot access my funds and I have bills due today."),
    ("Direct debit taken twice for same payment",
     "My energy provider's direct debit was taken twice this month, on the 1st and again on the 3rd. Please refund the duplicate."),
    ("Cannot access online banking",
     "I have been locked out of my online banking for 5 days. The password reset link in the email never arrives."),
    ("Bank transfer went to wrong account",
     "I accidentally sent £1,200 to the wrong sort code and account number. I need help recovering these funds urgently."),
    ("Overdraft fee applied incorrectly",
     "I was charged a £35 overdraft fee but my account showed a positive balance throughout the entire day in question."),
    ("Account statements not showing correct balance",
     "My paper statements and the app are showing two different balances — a difference of £520. Which is correct?"),
    ("Joint account holder removal request",
     "My relationship has ended and I need to remove my former partner from our joint account as quickly as possible."),
    ("Cheque deposited but funds not released",
     "I deposited a cheque for £800 a week ago. The funds are still on hold and I need them to pay urgent bills."),
    ("Recurring subscription charge I cannot identify",
     "A £14.99 charge appears on my account every month from 'SUBCRPTN SVCS'. I cannot identify or cancel this."),
    ("Request to close dormant savings account",
     "I have a savings account I have not used in 4 years. I would like to close it and transfer the balance to my current account."),
    ("Bank card not arrived after 3 weeks",
     "My replacement bank card was supposedly sent 3 weeks ago but has not arrived. I am currently unable to make any purchases."),

    # ── CREDIT CARD (12 cases) ─────────────────────────────────────────────
    ("Fraudulent credit card transaction",
     "I have just noticed a £799 charge on my credit card at an electronics store I have never visited. I need this investigated immediately."),
    ("Credit limit reduced without warning",
     "My credit limit was reduced from £5,000 to £2,000 without any prior notice. This has increased my utilisation ratio significantly."),
    ("Minimum payment due unclear",
     "My statement shows a minimum payment due but the figure seems much higher than normal. I need clarification on how it is calculated."),
    ("Cashback not credited to account",
     "I am owed £67.40 in cashback rewards from last quarter. The amount has not appeared in my account despite the promotional period ending."),
    ("Balance transfer not completed",
     "I requested a balance transfer of £2,000 from another card 10 days ago. The transfer has not appeared on either account."),
    ("Interest charged after paying full balance",
     "I paid my full statement balance on time but was still charged £23 in interest this month. Please explain why."),
    ("Credit card statement not received",
     "I have not received a paper or electronic statement for the past two months but charges are still being applied to my account."),
    ("Unable to add card to Apple Pay",
     "I am trying to add my credit card to Apple Pay but it keeps failing at the verification step. I have tried three times."),
    ("Dispute merchant charge after item returned",
     "I returned an item to an online retailer 3 weeks ago and they confirmed the refund, but my credit card still shows the charge."),
    ("Annual fee waiver request",
     "I have been a loyal customer for 8 years. I would like to request a waiver of the £120 annual fee on my credit card."),
    ("Card details stolen online",
     "I received a text alert for a purchase I did not make. I believe my card details have been compromised on an online site."),
    ("Promotional 0% interest rate expired early",
     "My promotional 0% balance transfer rate was supposed to last until December but interest started being charged in October."),

    # ── STUDENT LOAN (12 cases) ────────────────────────────────────────────
    ("Student loan repayment calculated incorrectly",
     "The amount being deducted from my salary for student loan repayment appears higher than what it should be based on my income."),
    ("Loan balance not updated after graduation",
     "It has been 6 months since I graduated and my loan balance still shows the same figure with no repayments credited."),
    ("Income-based repayment plan request",
     "My circumstances have changed significantly and I would like to apply for an income-based repayment plan."),
    ("Unable to defer loan during unemployment",
     "I was made redundant last month and am trying to defer my student loan payments but the online system keeps giving errors."),
    ("Loan interest rate seems too high",
     "My student loan interest rate is 7.3% but I understood it to be pegged to the RPI. The current RPI is 3.2%."),
    ("Incorrect graduation date on loan file",
     "My loan account shows a graduation date of 2021 but I graduated in 2022. This is affecting my repayment start date."),
    ("Request for student loan statement",
     "I am applying for a mortgage and require an official statement showing my student loan balance and monthly repayment amount."),
    ("Employer deducting loan payments when below threshold",
     "My salary is £22,000 which is below the repayment threshold. However my employer is still deducting student loan contributions."),
    ("Loan not paid to university on time",
     "My university is saying my loan instalment has not arrived for this term even though the loan company confirmed payment."),
    ("International student loan query",
     "I am moving abroad for work next year. I need information on how my student loan repayments will work as an overseas resident."),
    ("Multiple loans showing as one account",
     "I have two separate student loans from two different academic years but they appear merged into one account on my portal."),
    ("Request to suspend repayments during maternity leave",
     "I am going on maternity leave in two months. I would like to know the process for suspending my student loan repayments."),

    # ── OUT-OF-SCOPE / EDGE CASES (3 cases to test unknown routing) ────────
    ("Question about car insurance policy",
     "I want to understand the excess on my car insurance and whether my no-claims bonus transfers to a new vehicle."),
    ("Help with completing my tax return",
     "I am confused about which tax bracket I fall into and how to declare rental income on my self-assessment tax return."),
    ("Request for travel insurance recommendation",
     "I am travelling to Japan next month and need single-trip travel insurance that covers winter sports activities."),
]


def login(cred):
    """Authenticate and return Bearer token."""
    r = requests.post(f"{BASE_URL}/auth/login", json=cred, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]


def create_case(token, title, message):
    """POST /cases — no category/priority so AI decides everything."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": title,
        "message": message,
        "source": "web",
    }
    r = requests.post(f"{BASE_URL}/cases", json=payload, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def get_cases(token, page=1, page_size=100):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/cases", params={"page": page, "page_size": page_size},
                     headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


def print_banner(text, colour=Fore.CYAN):
    bar = "=" * 70
    print(f"\n{colour}{bar}")
    print(f"  {text}")
    print(f"{bar}{Style.RESET_ALL}\n")


# --- Main ------------------------------------------------------------------
def main():
    print_banner("CLARIX - End-to-End Dummy Data & AI Routing Test", Fore.MAGENTA)

    # 1. Login
    print(f"{Fore.YELLOW}>> Authenticating as customer...")
    try:
        token = login(CUST_CRED)
        print(f"{Fore.GREEN}  [OK] Logged in successfully.\n")
    except Exception as e:
        print(f"{Fore.RED}  [FAIL] Login failed: {e}")
        print(f"  Make sure the app is running and nginx is on http://localhost")
        return

    # 2. Create all cases
    print_banner(f"Creating {len(TEST_CASES)} test cases...", Fore.CYAN)

    results = []
    ai_routed = 0
    human_routed = 0
    out_of_scope = 0

    for i, (title, message) in enumerate(TEST_CASES, 1):
        try:
            case = create_case(token, title, message)

            team_id   = case.get("team_id") or ""
            team_name = TEAM_NAMES.get(team_id, f"Unknown ({team_id[:8]}...)")
            ai_cat    = case.get("ai_category") or "-"
            ai_pri    = case.get("ai_priority") or "-"
            ai_sent   = case.get("ai_sentiment") or "-"
            ai_conf   = case.get("ai_confidence")
            assigned  = case.get("assigned_to") or "-"

            is_ai_agent = (assigned == AI_AGENT_ID)

            if is_ai_agent:
                ai_routed += 1
            elif i > 72:  # last 3 are out-of-scope
                out_of_scope += 1
            else:
                human_routed += 1

            conf_str = f"{ai_conf:.2f}" if ai_conf else "-"

            results.append({
                "No.": i,
                "Title": title[:42] + "..." if len(title) > 42 else title,
                "AI Category": ai_cat,
                "AI Priority": ai_pri,
                "Sentiment": ai_sent,
                "Conf.": conf_str,
                "Team / Route": team_name,
                "AI Agent?": "YES" if is_ai_agent else "No",
            })

            # Progress every 10 cases
            if i % 10 == 0:
                print(f"  Created {i}/{len(TEST_CASES)} cases...")

        except Exception as e:
            print(f"{Fore.RED}  [FAIL] Case {i} ({title[:30]}): {e}")
            results.append({
                "No.": i,
                "Title": title[:42],
                "AI Category": "ERROR",
                "AI Priority": "-",
                "Sentiment": "-",
                "Conf.": "-",
                "Team / Route": str(e)[:30],
                "AI Agent?": "-",
            })

        time.sleep(0.3)  # gentle rate limiting

    # 3. Print results table
    print_banner("Results - AI Predictions & Routing", Fore.CYAN)
    rows = [[r["No."], r["Title"], r["AI Category"], r["AI Priority"],
             r["Sentiment"], r["Conf."], r["Team / Route"], r["AI Agent?"]]
            for r in results]
    print(tabulate(rows,
                   headers=["#", "Title", "AI Category", "AI Priority",
                             "Sentiment", "Conf.", "Team / Route", "AI Agent?"],
                   tablefmt="grid"))

    # 4. Summary
    print_banner("Summary", Fore.YELLOW)
    total = len(TEST_CASES)
    summary_rows = [
        ["Total cases created",             total],
        ["Routed to AI Agent (conf >0.85)",  ai_routed],
        ["Routed to human teams",            human_routed],
        ["Out-of-scope (defaulted to T1)",   out_of_scope],
    ]
    print(tabulate(summary_rows, headers=["Metric", "Count"], tablefmt="grid"))

    # 5. Routing breakdown by team
    print(f"\n{Fore.CYAN}--- Team Distribution ---")
    team_counts = {}
    for r in results:
        t = r["Team / Route"]
        team_counts[t] = team_counts.get(t, 0) + 1
    for team, count in sorted(team_counts.items(), key=lambda x: -x[1]):
        bar = "|" * count
        print(f"  {team:<25} {bar} ({count})")

    # 6. Wait for AI agent auto-resolution
    print_banner("Waiting 30s for AI Agent Auto-Resolution Loop...", Fore.YELLOW)
    print("  (The automation service polls every 10 seconds)")
    for i in range(30, 0, -5):
        print(f"  ... {i}s remaining...")
        time.sleep(5)

    # 7. Check resolution status via admin account
    print_banner("Checking AI Agent Resolution Status", Fore.CYAN)
    try:
        admin_token = login(ADMIN_CRED)
        cases_data  = get_cases(admin_token, page_size=100)
        items = cases_data if isinstance(cases_data, list) else cases_data.get("items", [])

        ai_assigned = [c for c in items if c.get("assigned_to") == AI_AGENT_ID]
        ai_resolved = [c for c in ai_assigned if c.get("status") in ("resolved", "closed")]
        ai_pending  = [c for c in ai_assigned if c.get("status") not in ("resolved", "closed")]

        print(f"  Cases assigned to AI Agent : {Fore.CYAN}{len(ai_assigned)}{Style.RESET_ALL}")
        print(f"  Auto-resolved by AI Agent  : {Fore.GREEN}{len(ai_resolved)}{Style.RESET_ALL}")
        print(f"  Still pending resolution   : {Fore.YELLOW}{len(ai_pending)}{Style.RESET_ALL}")

        if ai_resolved:
            print(f"\n{Fore.GREEN}  [RESOLVED] Auto-resolved cases:")
            for c in ai_resolved[:10]:
                print(f"    [OK] [{c.get('case_number')}] {c.get('title','')[:55]}")

        if ai_pending:
            print(f"\n{Fore.YELLOW}  [PENDING] Still awaiting resolution:")
            for c in ai_pending[:5]:
                print(f"    [...] [{c.get('case_number')}] {c.get('title','')[:55]}")

    except Exception as e:
        print(f"{Fore.RED}  Could not fetch resolution status: {e}")

    print_banner("[DONE] Test Complete! Open http://localhost/dashboard/cases to review.", Fore.GREEN)


if __name__ == "__main__":
    main()
