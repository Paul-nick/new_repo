#!/usr/bin/env python3
"""
Send personalized HTML emails via Gmail OAuth2 (no app passwords!).

Recipients (name + email) are read from a Google Sheet (published as CSV)
or from a local CSV file. Each message is personalized with the recipient's
name and sent with randomly chosen subject and HTML template.

Features:
  * OAuth2 authentication (use your actual Google account password)
  * Random subject selection
  * Random template/content selection
  * random 5-7 minute gap between messages
  * hard cap of 40 emails per calendar day
  * sent.csv log so re-runs never email the same person twice
  * Reconnection handling for network stability

Usage:
    python send_emails_v2.py --dry-run   # preview, sends nothing
    python send_emails_v2.py             # send (stops at the daily cap)

Config lives in a .env file next to this script (see .env.example).
"""

import csv
import io
import json
import os
import random
import sys
import time
import urllib.request
import pickle
from datetime import date
from email.message import EmailMessage
from email.utils import formataddr

import smtplib
import ssl

# Google Auth imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError

# --------------------------------------------------------------------------
# Pacing / limits
# --------------------------------------------------------------------------
DAILY_LIMIT = 40
MIN_DELAY_SECONDS = 5 * 60   # 5 minutes
MAX_DELAY_SECONDS = 7 * 60   # 7 minutes
SENT_LOG = "sent.csv"        # columns: date,email
TOKEN_PICKLE = "token.pickle"
CREDENTIALS_JSON = "credentials.json"

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# --------------------------------------------------------------------------
# Email templates (subjects and content pairs)
# --------------------------------------------------------------------------
EMAIL_TEMPLATES = [
    {
        "subject": "Remote collaboration with Jade Agency",
        "plain": """\
Hi {name},

I hope you're doing well.

I'm reaching out to see if you'd be open to a remote collaboration. We're \
currently connecting with full-stack developers who are comfortable speaking \
with clients in both English and Spanish.

The role mainly involves joining scheduled client calls, discussing your \
software development background, and helping present technical experience \
clearly. Our team provides guidance and preparation before each conversation.

If this sounds relevant to you, I'd be happy to share more details.

Best regards,
{sender}
Jade Agency
""",
        "html": """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <title>Jade Agency</title>
</head>
<body style="margin:0;padding:0;background-color:#eef1ef;font-family:'Segoe UI',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#eef1ef;font-size:1px;line-height:1px;">
    A remote collaboration for bilingual full-stack developers &mdash; from Jade Agency.
  </div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#eef1ef;padding:32px 12px;">
    <tr><td align="center">
      <table role="presentation" width="580" cellpadding="0" cellspacing="0" style="max-width:580px;width:100%;background-color:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e4e8e6;">
        <tr>
          <td style="background-color:#1E6F52;background-image:linear-gradient(135deg,#0C3B2E 0%,#1E6F52 50%,#2E9E7A 100%);padding:30px 40px;text-align:center;">
            <span style="color:#ffffff;font-size:24px;font-weight:700;letter-spacing:5px;">JADE AGENCY</span>
          </td>
        </tr>
        <tr>
          <td style="padding:38px 40px 34px 40px;color:#2A322F;font-size:16px;line-height:1.7;">
            <p style="margin:0 0 18px 0;">Hi {name},</p>
            <p style="margin:0 0 18px 0;">I hope you&rsquo;re doing well.</p>
            <p style="margin:0 0 18px 0;">
              I&rsquo;m reaching out to see if you&rsquo;d be open to a remote collaboration.
              We&rsquo;re currently connecting with full-stack developers who are comfortable
              speaking with clients in both English and Spanish.
            </p>
            <p style="margin:0 0 18px 0;">
              The role mainly involves joining scheduled client calls, discussing your
              software development background, and helping present technical experience
              clearly. Our team provides guidance and preparation before each conversation.
            </p>
            <p style="margin:0 0 26px 0;">
              If this sounds relevant to you, I&rsquo;d be happy to share more details.
            </p>
            <p style="margin:0 0 4px 0;">Best regards,</p>
            <p style="margin:0;font-weight:700;color:#0C3B2E;">{sender}</p>
            <p style="margin:2px 0 0 0;font-size:14px;color:#7a847f;">Jade Agency</p>
          </td>
        </tr>
        <tr>
          <td style="background-color:#f4f7f5;padding:18px 40px;border-top:1px solid #e4e8e6;color:#8a938e;font-size:12px;line-height:1.6;text-align:center;">
            You received this email from Jade Agency regarding a professional opportunity.<br>
            Not relevant? Reply
            <a href="mailto:{reply_email}?subject=Unsubscribe" style="color:#1E6F52;text-decoration:underline;">unsubscribe</a>
            and we won&rsquo;t contact you again.
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    },
    {
        "subject": "Join our developer network - Jade Agency",
        "plain": """\
Hi {name},

I've been impressed by your development work and thought you might be interested \
in a unique remote opportunity.

We're building a network of talented developers who work with our clients on \
diverse projects. The main commitment is participating in client calls where you \
share your experience and technical background.

No fixed hours—just meaningful work with great people. If interested, let's chat!

Best regards,
{sender}
Jade Agency
""",
        "html": """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <title>Jade Agency</title>
</head>
<body style="margin:0;padding:0;background-color:#eef1ef;font-family:'Segoe UI',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#eef1ef;font-size:1px;line-height:1px;">
    Join our developer network at Jade Agency &mdash; remote opportunities.
  </div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#eef1ef;padding:32px 12px;">
    <tr><td align="center">
      <table role="presentation" width="580" cellpadding="0" cellspacing="0" style="max-width:580px;width:100%;background-color:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e4e8e6;">
        <tr>
          <td style="background-color:#1E6F52;background-image:linear-gradient(135deg,#0C3B2E 0%,#1E6F52 50%,#2E9E7A 100%);padding:30px 40px;text-align:center;">
            <span style="color:#ffffff;font-size:24px;font-weight:700;letter-spacing:5px;">JADE AGENCY</span>
          </td>
        </tr>
        <tr>
          <td style="padding:38px 40px 34px 40px;color:#2A322F;font-size:16px;line-height:1.7;">
            <p style="margin:0 0 18px 0;">Hi {name},</p>
            <p style="margin:0 0 18px 0;">I&rsquo;ve been impressed by your development work and thought you might be interested in a unique remote opportunity.</p>
            <p style="margin:0 0 18px 0;">
              We&rsquo;re building a network of talented developers who work with our clients on
              diverse projects. The main commitment is participating in client calls where you
              share your experience and technical background.
            </p>
            <p style="margin:0 0 26px 0;">
              No fixed hours—just meaningful work with great people. If interested, let&rsquo;s chat!
            </p>
            <p style="margin:0 0 4px 0;">Best regards,</p>
            <p style="margin:0;font-weight:700;color:#0C3B2E;">{sender}</p>
            <p style="margin:2px 0 0 0;font-size:14px;color:#7a847f;">Jade Agency</p>
          </td>
        </tr>
        <tr>
          <td style="background-color:#f4f7f5;padding:18px 40px;border-top:1px solid #e4e8e6;color:#8a938e;font-size:12px;line-height:1.6;text-align:center;">
            You received this email from Jade Agency regarding a professional opportunity.<br>
            Not relevant? Reply
            <a href="mailto:{reply_email}?subject=Unsubscribe" style="color:#1E6F52;text-decoration:underline;">unsubscribe</a>
            and we won&rsquo;t contact you again.
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    }
]


def load_dotenv(path=".env"):
    """Minimal .env loader (no dependency). KEY=VALUE per line, # comments."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def authenticate_oauth2():
    """Authenticate with Gmail API using OAuth2."""
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token_file:
            creds = pickle.load(token_file)

    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing credentials...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_JSON):
                raise FileNotFoundError(
                    f"{CREDENTIALS_JSON} not found. "
                    "Download it from https://console.cloud.google.com/"
                )
            print("Starting OAuth2 authentication flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_JSON, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open(TOKEN_PICKLE, 'wb') as token_file:
            pickle.dump(creds, token_file)

    return creds


def get_gmail_user_from_creds(creds):
    """Extract email from OAuth2 credentials."""
    return creds.token_info.get('email', '') if hasattr(creds, 'token_info') else ''


def send_via_smtp_oauth2(gmail_user, access_token, recipient, template, sender_name):
    """Send email via Gmail SMTP using OAuth2 access token."""
    msg = EmailMessage()
    msg["From"] = formataddr((f"{sender_name} | Jade Agency", gmail_user))
    msg["To"] = recipient["email"]
    msg["Subject"] = template["subject"]
    msg.set_content(template["plain"].format(name=recipient["name"], sender=sender_name))
    msg.add_alternative(
        template["html"].format(
            name=recipient["name"], sender=sender_name, reply_email=gmail_user
        ),
        subtype="html",
    )

    # Gmail SMTP with OAuth2
    auth_string = f"user={gmail_user}\x01auth=Bearer {access_token}\x01\x01"

    context = ssl.create_default_context()
    server = smtplib.SMTP("smtp.gmail.com", 587, context=context, timeout=30)
    server.starttls()
    server.authenticate('XOAUTH2', lambda x: auth_string.encode())
    server.send_message(msg)
    server.quit()


def read_recipients():
    """Return list of {name, email} dicts from the Google Sheet or local CSV."""
    name_col = os.environ.get("NAME_COLUMN", "name")
    email_col = os.environ.get("EMAIL_COLUMN", "email")
    sheet_url = os.environ.get("SHEET_CSV_URL", "").strip()

    if sheet_url:
        print("Reading recipients from Google Sheet CSV...")
        with urllib.request.urlopen(sheet_url) as resp:
            text = resp.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
    else:
        path = os.environ.get("CONTACTS_CSV", "contacts.csv")
        print(f"Reading recipients from {path} ...")
        f = open(path, newline="", encoding="utf-8-sig")
        reader = csv.DictReader(f)

    recipients = []
    for row in reader:
        norm = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        email = norm.get(email_col.lower(), "")
        name = norm.get(name_col.lower(), "")
        if not email or "@" not in email:
            continue
        recipients.append({"name": name or "there", "email": email})
    return recipients


def load_sent():
    """Return (all_sent_emails set, count_sent_today)."""
    sent = set()
    today_count = 0
    today = date.today().isoformat()
    if os.path.exists(SENT_LOG):
        with open(SENT_LOG, newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) < 2:
                    continue
                d, email = row[0].strip(), row[1].strip().lower()
                sent.add(email)
                if d == today:
                    today_count += 1
    return sent, today_count


def mark_sent(email):
    new_file = not os.path.exists(SENT_LOG)
    with open(SENT_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["date", "email"])
        w.writerow([date.today().isoformat(), email.lower()])


def main():
    load_dotenv()
    dry_run = "--dry-run" in sys.argv

    sender_name = os.environ.get("SENDER_NAME", "Collaborator").strip()

    # Authenticate with OAuth2
    try:
        creds = authenticate_oauth2()
        gmail_user = creds.token_info.get('email', os.environ.get('GMAIL_USER', ''))
        if not gmail_user:
            sys.exit("ERROR: Could not determine Gmail user from credentials.")
        access_token = creds.token
    except Exception as e:
        sys.exit(f"ERROR: Authentication failed: {e}")

    recipients = read_recipients()
    already, today_count = load_sent()
    pending = [r for r in recipients if r["email"].lower() not in already]

    remaining_today = max(0, DAILY_LIMIT - today_count)
    print(f"Total recipients: {len(recipients)} | already emailed: {len(already)}")
    print(f"Sent today: {today_count}/{DAILY_LIMIT} | remaining today: {remaining_today}")
    print(f"Queue (not yet emailed): {len(pending)}")
    print(f"Available templates: {len(EMAIL_TEMPLATES)}")

    if dry_run:
        print("\n=== DRY RUN (nothing will be sent) ===")
        if pending:
            template = random.choice(EMAIL_TEMPLATES)
            print(f"Subject: {template['subject']}")
            print(f"To (first 5): {[r['email'] for r in pending[:5]]}")
            print(f"Would send today: {min(len(pending), remaining_today)} "
                  f"(cap {DAILY_LIMIT}/day, ~5-7 min apart)")
            html_path = "preview.html"
            with open(html_path, "w", encoding="utf-8") as fh:
                fh.write(template["html"].format(
                    name=pending[0]["name"], sender=sender_name, reply_email=gmail_user
                ))
            print(f"HTML preview written to {html_path} (open it in a browser)")
        return

    if remaining_today <= 0:
        print("\nDaily limit reached. Run again tomorrow to continue.")
        return
    if not pending:
        print("\nEveryone in the list has already been emailed. Nothing to do.")
        return

    to_send = pending[:remaining_today]
    print(f"\nSending {len(to_send)} email(s) now, {MIN_DELAY_SECONDS//60}-"
          f"{MAX_DELAY_SECONDS//60} min apart. Ctrl+C to stop (progress is saved).")

    sent = 0
    for i, r in enumerate(to_send, 1):
        template = random.choice(EMAIL_TEMPLATES)

        try:
            send_via_smtp_oauth2(gmail_user, access_token, r, template, sender_name)
            mark_sent(r["email"])
            sent += 1
            print(f"[{i}/{len(to_send)}] sent to {r['email']} ({r['name']}) - subject: {template['subject'][:40]}...")
        except RefreshError:
            print(f"[{i}/{len(to_send)}] Token expired. Please re-authenticate.")
            # Delete token to force re-authentication on next run
            if os.path.exists(TOKEN_PICKLE):
                os.remove(TOKEN_PICKLE)
            break
        except Exception as e:
            print(f"[{i}/{len(to_send)}] FAILED {r['email']}: {e}")

        if i < len(to_send):
            wait = random.randint(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
            print(f"    waiting {wait//60}m {wait%60}s before next...")
            time.sleep(wait)

    print(f"\nDone. Sent {sent} this run. Today's total: {today_count + sent}/{DAILY_LIMIT}.")


if __name__ == "__main__":
    main()
