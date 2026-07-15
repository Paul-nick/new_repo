# Installation & Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install PyQt5 google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Get Google Credentials
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable the **Gmail API**
4. Create OAuth 2.0 credentials (**Desktop Application**)
5. Download the JSON file and save as `credentials.json` in your project folder

### 3. Prepare Your Data
Create a `contacts.csv` file with columns: `name`, `email`
```csv
name,email
John Doe,john@example.com
Jane Smith,jane@example.com
```

### 4. Run the GUI Application
```bash
python send_emails_gui.py
```

## Build Windows EXE

To create a standalone `.exe` file (no Python required):

```bash
pip install pyinstaller
python build_exe.py
```

The EXE will be created at: `dist/EmailSender.exe`

## File Structure

```
your_project/
├── send_emails_gui.py          # Main GUI application
├── send_emails_v2.py           # Command-line version (optional)
├── build_exe.py                # Build script for EXE
├── credentials.json            # Google API credentials (download from Google Cloud)
├── contacts.csv                # Your recipient list
├── token.pickle                # Auto-generated after first login
└── sent.csv                    # Auto-generated log of sent emails
```

## Features

✅ **OAuth2 Authentication** - No App Passwords needed
✅ **5 Tabs Interface:**
  - Setup & Config (login, settings)
  - Recipients (load CSV, view status)
  - Templates (preview emails)
  - Send Emails (send with progress tracking)
  - Logs & History (view sent emails)

✅ **Smart Features:**
  - Random template selection
  - Random 5-7 min delays between emails
  - Daily limit (40 by default)
  - Dry-run mode (preview without sending)
  - Pause/Resume functionality
  - Never re-sends to same person (sent.csv tracking)

## Troubleshooting

**"credentials.json not found"**
→ Download from Google Cloud Console and place in the same folder as the script

**"Authentication failed"**
→ Make sure you've enabled the Gmail API in Google Cloud Console

**PyInstaller not found**
→ Run: `pip install pyinstaller`

**"Module not found" errors**
→ Install all dependencies: `pip install -r requirements.txt`
