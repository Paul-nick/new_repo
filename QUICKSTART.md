# Quick Start Guide - Jade Agency Email Sender

## 5-Minute Setup

### Step 1: Install Python Packages
```bash
pip install -r requirements.txt
```

### Step 2: Get Google Credentials
1. Go to **https://console.cloud.google.com/**
2. Create a new project (name it "Jade Agency")
3. Search for "Gmail API" and click **Enable**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Choose **Desktop Application**
6. Click **Create**
7. Download the JSON file
8. Rename it to `credentials.json` and place in your project folder

### Step 3: Prepare Your Contact List
Create `contacts.csv`:
```csv
name,email
John Doe,john@example.com
Jane Smith,jane@example.com
```

Or copy from the example:
```bash
cp contacts_example.csv contacts.csv
```

### Step 4: Run the GUI
```bash
python send_emails_gui.py
```

### Step 5: In the GUI
1. **Setup Tab**: Click "Login with Google Account" (browser window opens)
2. **Recipients Tab**: Click "Browse CSV" → select your contacts.csv
3. **Recipients Tab**: Click "Load Recipients"
4. **Send Tab**: Click "Start Sending" (or "Dry Run" to preview first)

✅ **Done!** Your emails are being sent with random templates, 5-7 min delays, and automatic tracking.

---

## Build as Windows EXE (No Python Required)

```bash
python build_exe.py
```

Then find `dist/EmailSender.exe` - you can share this file with others!

**To use the EXE:**
1. Place `credentials.json` in the same folder as `EmailSender.exe`
2. Create `contacts.csv` with your recipients
3. Double-click `EmailSender.exe`

---

## Features Overview

✅ **Tab 1: Setup & Config**
- Login with your actual Google account (OAuth2)
- Set sender name, daily limit, email delays

✅ **Tab 2: Recipients**
- Load CSV file with names and emails
- See which recipients have already been emailed
- View today's count vs daily limit

✅ **Tab 3: Templates**
- Preview the 2 different email templates
- See subject and content before sending

✅ **Tab 4: Send Emails**
- **Dry Run**: Preview without sending anything
- **Start Sending**: Send with random 5-7 min delays
- **Pause/Resume**: Stop mid-send and continue later
- Real-time progress and status log

✅ **Tab 5: Logs & History**
- View all sent emails with dates
- Clear logs if needed

---

## Automatic Tracking

Every time you send emails:
- **sent.csv** is updated (never re-emails same person)
- **token.pickle** stores your login (no re-auth needed)
- Progress is saved if you pause/stop

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "credentials.json not found" | Download from Google Cloud Console (Step 2 above) |
| "Module not found" | Run `pip install -r requirements.txt` |
| "Authentication failed" | Make sure Gmail API is enabled in Google Cloud |
| PyInstaller errors | Update: `pip install --upgrade pyinstaller` |
| EXE won't run | Copy `credentials.json` to same folder as `.exe` |

---

## Command-Line Alternative

For advanced users, you can also use the CLI version:
```bash
python send_emails_v2.py --dry-run    # Preview
python send_emails_v2.py              # Send for real
```

---

## Security Notes

✅ **Your credentials are safe:**
- OAuth2 means you use your actual Gmail password (Google handles it)
- No App Passwords stored locally
- `token.pickle` is encrypted and only readable by your user
- Never share `credentials.json` - it's your Google OAuth key

---

## Support

If something breaks:
1. Check README.md for more details
2. Delete `token.pickle` to force re-authentication
3. Check that `credentials.json` is valid JSON

Questions? Check the GitHub repo or create an issue.
