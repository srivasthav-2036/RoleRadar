"""
email_sender.py

Sends "new jobs found" notification emails via Brevo's transactional
email API (free tier: 300 emails/day, no credit card required).

Setup needed (one-time, in Brevo dashboard):
1. Create a free account at brevo.com
2. Verify a sender email (Settings -> Senders & IP)
3. Get your API key (Settings -> API Keys)
4. Set BREVO_API_KEY and BREVO_SENDER_EMAIL as env vars / GitHub secrets

WEBSITE_BASE_URL is optional (per the user's "this feature is
optional" note). If set, each job card and the "+N more" link point
to the recommendations page on your site. If unset, the email still
works - it just renders as plain, unlinked cards.
"""

import os

import requests

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"

SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")
SENDER_NAME = "RoleRadar"

WEBSITE_BASE_URL = os.getenv("WEBSITE_BASE_URL")  # e.g. "https://roleradar.example.com"

MAX_DISPLAY = 5


def _job_card_html(rec: dict) -> str:
    """
    Minimal card: title, company, score only - no description, no
    skills, no other clutter. That's deliberate; the email is a
    nudge, not the full detail view.
    """
    job = rec["job"]
    score = rec.get("score", "")
    title = job.get("title", "")
    company = job.get("company", "")
    job_id = job.get("job_id", "")

    if WEBSITE_BASE_URL:
        open_tag = (
            f'<a href="{WEBSITE_BASE_URL}/recommendations?job_id={job_id}" '
            f'style="text-decoration:none;color:inherit;display:block;">'
        )
        close_tag = "</a>"
    else:
        open_tag = ""
        close_tag = ""

    return f"""
    <tr>
        <td style="padding:0 0 10px 0;">
            <div style="border:1px solid #e3e3e3;border-radius:8px;padding:12px 14px;">
                {open_tag}
                <div style="font-weight:bold;font-size:15px;color:#111;">{title}</div>
                <div style="color:#555;font-size:13px;margin-top:2px;">{company}</div>
                <div style="color:#1a7f4b;font-size:12px;margin-top:6px;">Match Score: {score}</div>
                {close_tag}
            </div>
        </td>
    </tr>
    """


def _build_html(matched_jobs: list[dict]) -> str:
    total = len(matched_jobs)
    shown = matched_jobs[:MAX_DISPLAY]
    remaining = total - len(shown)

    cards_html = "".join(_job_card_html(rec) for rec in shown)

    if remaining > 0:
        if WEBSITE_BASE_URL:
            more_html = (
                f'<p style="margin-top:6px;">'
                f'<a href="{WEBSITE_BASE_URL}/recommendations">+{remaining} more on RoleRadar</a>'
                f"</p>"
            )
        else:
            more_html = f'<p style="margin-top:6px;">+{remaining} more waiting for you on RoleRadar</p>'
    else:
        more_html = ""

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;">
        <h2 style="margin-bottom:14px;">
            {total} new job match{'es' if total != 1 else ''} found on RoleRadar
        </h2>
        <table style="width:100%;border-collapse:collapse;">
            {cards_html}
        </table>
        {more_html}
    </body>
    </html>
    """


def send_new_jobs_email(to_email: str, matched_jobs: list[dict]):
    """
    Sends one email to to_email listing matched_jobs (top 5 shown as
    cards, rest summarized as "+N more"). Silently does nothing if
    matched_jobs is empty.
    """
    if not matched_jobs:
        return

    total = len(matched_jobs)

    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": (
            f"{total} new job match{'es' if total != 1 else ''} found on RoleRadar"
        ),
        "htmlContent": _build_html(matched_jobs),
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    response = requests.post(
        BREVO_SEND_URL, json=payload, headers=headers, timeout=15
    )

    if response.status_code >= 300:
        print(
            f"[email_sender] FAILED to send to {to_email}: "
            f"{response.status_code} {response.text}"
        )
    else:
        print(f"[email_sender] Sent to {to_email}")


def send_welcome_email(to_email: str):
    """
    Sends a one-time welcome email when a new user registers.
    Introduces RoleRadar and sets expectations about how the platform works.
    """
    if not BREVO_API_KEY or not SENDER_EMAIL:
        print("[email_sender] Skipping welcome email — Brevo not configured.")
        return

    dashboard_link = f"{WEBSITE_BASE_URL}/dashboard" if WEBSITE_BASE_URL else "#"
    resume_link = f"{WEBSITE_BASE_URL}/dashboard/resume" if WEBSITE_BASE_URL else "#"

    html_content = f"""
    <html>
    <body style="font-family:Arial,sans-serif;background:#f9f9f7;margin:0;padding:0;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9f9f7;padding:32px 0;">
        <tr>
          <td align="center">
            <table width="560" cellpadding="0" cellspacing="0"
                   style="background:#ffffff;border-radius:12px;border:1px solid #e5e5e0;padding:40px 36px;max-width:560px;">
              <tr>
                <td>
                  <!-- Logo/brand -->
                  <div style="margin-bottom:28px;">
                    <span style="font-size:18px;font-weight:600;color:#111;letter-spacing:-0.3px;">
                      ● RoleRadar
                    </span>
                  </div>

                  <!-- Headline -->
                  <h1 style="font-size:22px;font-weight:600;color:#111;margin:0 0 12px 0;
                              letter-spacing:-0.3px;line-height:1.3;">
                    Welcome to RoleRadar 👋
                  </h1>
                  <p style="font-size:14px;color:#555;line-height:1.7;margin:0 0 20px 0;">
                    You're now part of a smarter way to discover job opportunities.
                    RoleRadar uses AI to match your resume against real job listings
                    and sends you personalised recommendations directly to your inbox.
                  </p>

                  <!-- How it works -->
                  <div style="background:#f5f5f0;border-radius:8px;padding:20px 20px;margin-bottom:24px;">
                    <p style="font-size:12px;font-weight:700;color:#888;text-transform:uppercase;
                               letter-spacing:0.1em;margin:0 0 14px 0;">How it works</p>
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="padding:0 0 12px 0;">
                          <div style="font-size:14px;color:#333;line-height:1.5;">
                            <strong style="color:#111;">1. Upload your resume</strong><br>
                            Our AI parses your experience, skills, and projects.
                          </div>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:0 0 12px 0;">
                          <div style="font-size:14px;color:#333;line-height:1.5;">
                            <strong style="color:#111;">2. We scan job listings</strong><br>
                            Every few hours, RoleRadar fetches new opportunities and
                            scores them against your profile.
                          </div>
                        </td>
                      </tr>
                      <tr>
                        <td>
                          <div style="font-size:14px;color:#333;line-height:1.5;">
                            <strong style="color:#111;">3. Receive personalised matches</strong><br>
                            Get email alerts for your top-matching roles with AI match scores.
                          </div>
                        </td>
                      </tr>
                    </table>
                  </div>

                  <!-- CTA -->
                  <div style="margin-bottom:28px;">
                    <a href="{resume_link}"
                       style="display:inline-block;background:#111;color:#fff;text-decoration:none;
                              font-size:13px;font-weight:600;padding:11px 22px;border-radius:100px;">
                      Upload Your Resume →
                    </a>
                  </div>

                  <!-- Note -->
                  <div style="border-top:1px solid #e5e5e0;padding-top:20px;">
                    <p style="font-size:12.5px;color:#888;line-height:1.6;margin:0;">
                      <strong>Note:</strong> RoleRadar currently searches a limited number of job
                      providers. We're continuously adding more sources. In the meantime, we
                      recommend continuing to search other job platforms as well.
                    </p>
                    <p style="font-size:12px;color:#aaa;margin:12px 0 0 0;">
                      Found a bug? Email us at
                      <a href="mailto:roleradar.notifications@gmail.com"
                         style="color:#888;">roleradar.notifications@gmail.com</a>
                    </p>
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": "Welcome to RoleRadar — your AI job matcher is ready",
        "htmlContent": html_content,
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    try:
        response = requests.post(
            BREVO_SEND_URL, json=payload, headers=headers, timeout=15
        )
        if response.status_code >= 300:
            print(
                f"[email_sender] FAILED welcome email to {to_email}: "
                f"{response.status_code} {response.text}"
            )
        else:
            print(f"[email_sender] Welcome email sent to {to_email}")
    except Exception as e:
        print(f"[email_sender] Error sending welcome email: {e}")