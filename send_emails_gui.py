#!/usr/bin/env python3
"""
GUI Application for sending emails via Gmail OAuth2.
Built with PyQt5 for a professional, intuitive interface.

Features:
  * Email account login (OAuth2)
  * CSV recipient file selector
  * Template preview/editor
  * Real-time send progress with pause/resume
  * Settings configuration (daily limit, delays)
  * Logs viewer
  * Dry-run mode

Usage:
    python send_emails_gui.py
"""

import sys
import os
import csv
import random
import threading
import time
from datetime import date
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit, QTabWidget,
    QTableWidget, QTableWidgetItem, QSpinBox, QComboBox, QCheckBox,
    QProgressBar, QMessageBox, QDialog, QFormLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon

# Import the send_emails_v2 logic
import pickle
from email.message import EmailMessage
from email.utils import formataddr
import smtplib
import ssl
import io
import urllib.request

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError

# --------------------------------------------------------------------------
# Email templates (same as send_emails_v2.py)
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
  <title>Jade Agency</title>
</head>
<body style="margin:0;padding:0;background-color:#eef1ef;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
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
  <title>Jade Agency</title>
</head>
<body style="margin:0;padding:0;background-color:#eef1ef;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
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

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_PICKLE = "token.pickle"
CREDENTIALS_JSON = "credentials.json"
SENT_LOG = "sent.csv"


# --------------------------------------------------------------------------
# Worker thread for sending emails
# --------------------------------------------------------------------------
class EmailSenderThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, int)  # success, count
    
    def __init__(self, recipients, gmail_user, access_token, sender_name, dry_run=False):
        super().__init__()
        self.recipients = recipients
        self.gmail_user = gmail_user
        self.access_token = access_token
        self.sender_name = sender_name
        self.dry_run = dry_run
        self.running = True
        self.paused = False
        
    def run(self):
        if self.dry_run:
            self._dry_run()
            return
        
        sent = 0
        for i, r in enumerate(self.recipients):
            if not self.running:
                break
            
            while self.paused and self.running:
                time.sleep(0.5)
            
            if not self.running:
                break
            
            template = random.choice(EMAIL_TEMPLATES)
            try:
                self._send_email(r, template)
                self._mark_sent(r["email"])
                sent += 1
                self.status.emit(f"✓ Sent to {r['email']} ({r['name']})")
            except Exception as e:
                self.status.emit(f"✗ Failed: {r['email']} - {str(e)}")
            
            self.progress.emit(i + 1)
            
            if i < len(self.recipients) - 1:
                time.sleep(random.randint(300, 420))  # 5-7 minutes
        
        self.finished.emit(True, sent)
    
    def _dry_run(self):
        self.status.emit("DRY RUN MODE - No emails will be sent")
        for i, r in enumerate(self.recipients):
            template = random.choice(EMAIL_TEMPLATES)
            self.status.emit(f"[DRY] Would send to {r['email']} - Subject: {template['subject']}")
            self.progress.emit(i + 1)
            time.sleep(0.5)
        self.finished.emit(True, 0)
    
    def _send_email(self, recipient, template):
        msg = EmailMessage()
        msg["From"] = formataddr((f"{self.sender_name} | Jade Agency", self.gmail_user))
        msg["To"] = recipient["email"]
        msg["Subject"] = template["subject"]
        msg.set_content(template["plain"].format(name=recipient["name"], sender=self.sender_name))
        msg.add_alternative(
            template["html"].format(
                name=recipient["name"], sender=self.sender_name, reply_email=self.gmail_user
            ),
            subtype="html",
        )
        
        auth_string = f"user={self.gmail_user}\x01auth=Bearer {self.access_token}\x01\x01"
        context = ssl.create_default_context()
        server = smtplib.SMTP("smtp.gmail.com", 587, context=context, timeout=30)
        server.starttls()
        server.authenticate('XOAUTH2', lambda x: auth_string.encode())
        server.send_message(msg)
        server.quit()
    
    def _mark_sent(self, email):
        new_file = not os.path.exists(SENT_LOG)
        with open(SENT_LOG, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(["date", "email"])
            w.writerow([date.today().isoformat(), email.lower()])
    
    def pause(self):
        self.paused = True
    
    def resume(self):
        self.paused = False
    
    def stop(self):
        self.running = False


# --------------------------------------------------------------------------
# Main GUI Application
# --------------------------------------------------------------------------
class EmailSenderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.gmail_user = None
        self.access_token = None
        self.recipients = []
        self.sender_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Jade Agency - Email Sender")
        self.setGeometry(100, 100, 1000, 700)
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Tab widget
        tabs = QTabWidget()
        
        # Tab 1: Setup
        setup_tab = self.create_setup_tab()
        tabs.addTab(setup_tab, "Setup & Config")
        
        # Tab 2: Recipients
        recipients_tab = self.create_recipients_tab()
        tabs.addTab(recipients_tab, "Recipients")
        
        # Tab 3: Templates
        templates_tab = self.create_templates_tab()
        tabs.addTab(templates_tab, "Templates")
        
        # Tab 4: Send
        send_tab = self.create_send_tab()
        tabs.addTab(send_tab, "Send Emails")
        
        # Tab 5: Logs
        logs_tab = self.create_logs_tab()
        tabs.addTab(logs_tab, "Logs & History")
        
        main_layout.addWidget(tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QPushButton { 
                background-color: #1E6F52; 
                color: white; 
                border: none; 
                padding: 8px 16px; 
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0C3B2E; }
            QPushButton:pressed { background-color: #0a2b22; }
            QLineEdit, QTextEdit { 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                padding: 6px;
            }
            QLabel { color: #2A322F; font-weight: 500; }
        """)
    
    def create_setup_tab(self):
        widget = QWidget()
        layout = QFormLayout()
        
        # OAuth2 Login
        self.oauth_btn = QPushButton("Login with Google Account")
        self.oauth_btn.clicked.connect(self.login_oauth2)
        self.oauth_status = QLabel("Not authenticated")
        self.oauth_status.setStyleSheet("color: red;")
        
        layout.addRow("Google Account:", self.oauth_btn)
        layout.addRow("Status:", self.oauth_status)
        
        # Sender name
        self.sender_name_input = QLineEdit("Paul")
        layout.addRow("Sender Name:", self.sender_name_input)
        
        # Settings
        layout.addRow(QLabel("\n=== Settings ==="))
        
        self.daily_limit_spinbox = QSpinBox()
        self.daily_limit_spinbox.setValue(40)
        self.daily_limit_spinbox.setMaximum(200)
        layout.addRow("Daily Email Limit:", self.daily_limit_spinbox)
        
        self.min_delay_spinbox = QSpinBox()
        self.min_delay_spinbox.setValue(5)
        self.min_delay_spinbox.setMaximum(60)
        layout.addRow("Min Delay (minutes):", self.min_delay_spinbox)
        
        self.max_delay_spinbox = QSpinBox()
        self.max_delay_spinbox.setValue(7)
        self.max_delay_spinbox.setMaximum(60)
        layout.addRow("Max Delay (minutes):", self.max_delay_spinbox)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_recipients_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # File selector
        file_layout = QHBoxLayout()
        self.file_path_label = QLineEdit()
        self.file_path_label.setReadOnly(True)
        self.file_path_label.setPlaceholderText("No file selected")
        file_btn = QPushButton("Browse CSV")
        file_btn.clicked.connect(self.select_csv_file)
        file_layout.addWidget(QLabel("CSV File:"))
        file_layout.addWidget(self.file_path_label)
        file_layout.addWidget(file_btn)
        layout.addLayout(file_layout)
        
        # Column mapping
        col_layout = QHBoxLayout()
        self.name_col_input = QLineEdit("name")
        self.email_col_input = QLineEdit("email")
        col_layout.addWidget(QLabel("Name Column:"))
        col_layout.addWidget(self.name_col_input)
        col_layout.addWidget(QLabel("Email Column:"))
        col_layout.addWidget(self.email_col_input)
        layout.addLayout(col_layout)
        
        # Load button
        load_btn = QPushButton("Load Recipients")
        load_btn.clicked.connect(self.load_recipients)
        layout.addWidget(load_btn)
        
        # Recipients table
        self.recipients_table = QTableWidget()
        self.recipients_table.setColumnCount(3)
        self.recipients_table.setHorizontalHeaderLabels(["Name", "Email", "Status"])
        self.recipients_table.setColumnWidth(0, 200)
        self.recipients_table.setColumnWidth(1, 250)
        self.recipients_table.setColumnWidth(2, 150)
        layout.addWidget(self.recipients_table)
        
        # Stats
        self.recipients_stats = QLabel()
        layout.addWidget(self.recipients_stats)
        
        widget.setLayout(layout)
        return widget
    
    def create_templates_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Template selector
        selector_layout = QHBoxLayout()
        self.template_combo = QComboBox()
        for i, t in enumerate(EMAIL_TEMPLATES):
            self.template_combo.addItem(f"Template {i+1}: {t['subject']}")
        self.template_combo.currentIndexChanged.connect(self.show_template)
        selector_layout.addWidget(QLabel("Select Template:"))
        selector_layout.addWidget(self.template_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Subject
        layout.addWidget(QLabel("Subject:"))
        self.subject_display = QLineEdit()
        self.subject_display.setReadOnly(True)
        layout.addWidget(self.subject_display)
        
        # Plain text preview
        layout.addWidget(QLabel("Plain Text Preview:"))
        self.plain_preview = QTextEdit()
        self.plain_preview.setReadOnly(True)
        layout.addWidget(self.plain_preview)
        
        # HTML preview
        layout.addWidget(QLabel("HTML Preview (first 500 chars):"))
        self.html_preview = QTextEdit()
        self.html_preview.setReadOnly(True)
        layout.addWidget(self.html_preview)
        
        self.show_template()
        widget.setLayout(layout)
        return widget
    
    def create_send_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Mode selection
        mode_layout = QHBoxLayout()
        self.dry_run_checkbox = QCheckBox("Dry Run (preview only)")
        mode_layout.addWidget(self.dry_run_checkbox)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Send buttons
        btn_layout = QHBoxLayout()
        self.send_btn = QPushButton("Start Sending")
        self.send_btn.clicked.connect(self.start_sending)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_sending)
        self.pause_btn.setEnabled(False)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_sending)
        self.stop_btn.setEnabled(False)
        
        btn_layout.addWidget(self.send_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Progress
        layout.addWidget(QLabel("Progress:"))
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Status log
        layout.addWidget(QLabel("Status Log:"))
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        layout.addWidget(self.status_log)
        
        # Summary
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-weight: bold; color: #1E6F52;")
        layout.addWidget(self.summary_label)
        
        widget.setLayout(layout)
        return widget
    
    def create_logs_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Logs")
        refresh_btn.clicked.connect(self.refresh_logs)
        clear_btn = QPushButton("Clear Sent Log")
        clear_btn.clicked.connect(self.clear_logs)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(2)
        self.logs_table.setHorizontalHeaderLabels(["Date", "Email"])
        self.logs_table.setColumnWidth(0, 150)
        self.logs_table.setColumnWidth(1, 300)
        layout.addWidget(self.logs_table)
        
        self.refresh_logs()
        widget.setLayout(layout)
        return widget
    
    def login_oauth2(self):
        try:
            if not os.path.exists(CREDENTIALS_JSON):
                QMessageBox.critical(self, "Error", 
                    f"credentials.json not found. Download from https://console.cloud.google.com/")
                return
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_JSON, SCOPES)
            creds = flow.run_local_server(port=0)
            
            with open(TOKEN_PICKLE, 'wb') as f:
                pickle.dump(creds, f)
            
            self.gmail_user = creds.token_info.get('email', '')
            self.access_token = creds.token
            
            self.oauth_status.setText(f"✓ Authenticated as {self.gmail_user}")
            self.oauth_status.setStyleSheet("color: green;")
            self.oauth_btn.setText("Re-authenticate")
            
            QMessageBox.information(self, "Success", f"Logged in as {self.gmail_user}")
        except Exception as e:
            QMessageBox.critical(self, "Auth Error", str(e))
    
    def select_csv_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if path:
            self.file_path_label.setText(path)
    
    def load_recipients(self):
        if not self.file_path_label.text():
            QMessageBox.warning(self, "Warning", "Please select a CSV file first")
            return
        
        try:
            name_col = self.name_col_input.text().lower()
            email_col = self.email_col_input.text().lower()
            
            with open(self.file_path_label.text(), newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                self.recipients = []
                for row in reader:
                    norm = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
                    email = norm.get(email_col, "")
                    name = norm.get(name_col, "")
                    if email and "@" in email:
                        self.recipients.append({"name": name or "there", "email": email})
            
            self._update_recipients_table()
            QMessageBox.information(self, "Success", f"Loaded {len(self.recipients)} recipients")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def _update_recipients_table(self):
        self.recipients_table.setRowCount(len(self.recipients))
        
        sent_emails = self._load_sent_emails()
        for i, r in enumerate(self.recipients):
            self.recipients_table.setItem(i, 0, QTableWidgetItem(r["name"]))
            self.recipients_table.setItem(i, 1, QTableWidgetItem(r["email"]))
            
            status = "Sent" if r["email"].lower() in sent_emails else "Pending"
            item = QTableWidgetItem(status)
            if status == "Sent":
                item.setForeground(QColor("gray"))
            self.recipients_table.setItem(i, 2, item)
        
        today_count = self._count_sent_today()
        self.recipients_stats.setText(
            f"Total: {len(self.recipients)} | Already sent: {len(sent_emails)} | "
            f"Today: {today_count}/{self.daily_limit_spinbox.value()}"
        )
    
    def _load_sent_emails(self):
        sent = set()
        if os.path.exists(SENT_LOG):
            with open(SENT_LOG, newline="", encoding="utf-8") as f:
                for row in csv.reader(f):
                    if len(row) >= 2:
                        sent.add(row[1].strip().lower())
        return sent
    
    def _count_sent_today(self):
        count = 0
        today = date.today().isoformat()
        if os.path.exists(SENT_LOG):
            with open(SENT_LOG, newline="", encoding="utf-8") as f:
                for row in csv.reader(f):
                    if len(row) >= 1 and row[0].strip() == today:
                        count += 1
        return count
    
    def show_template(self):
        idx = self.template_combo.currentIndex()
        if 0 <= idx < len(EMAIL_TEMPLATES):
            template = EMAIL_TEMPLATES[idx]
            self.subject_display.setText(template["subject"])
            self.plain_preview.setText(template["plain"][:500])
            self.html_preview.setText(template["html"][:500])
    
    def start_sending(self):
        if not self.gmail_user:
            QMessageBox.warning(self, "Warning", "Please authenticate first")
            return
        
        if not self.recipients:
            QMessageBox.warning(self, "Warning", "Please load recipients first")
            return
        
        sent_emails = self._load_sent_emails()
        pending = [r for r in self.recipients if r["email"].lower() not in sent_emails]
        
        if not pending:
            QMessageBox.information(self, "Info", "All recipients have been emailed")
            return
        
        self.sender_thread = EmailSenderThread(
            pending, self.gmail_user, self.access_token, 
            self.sender_name_input.text(),
            self.dry_run_checkbox.isChecked()
        )
        self.sender_thread.progress.connect(self.update_progress)
        self.sender_thread.status.connect(self.update_status)
        self.sender_thread.finished.connect(self.sending_finished)
        
        self.send_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.status_log.clear()
        self.progress_bar.setMaximum(len(pending))
        self.progress_bar.setValue(0)
        
        self.sender_thread.start()
    
    def pause_sending(self):
        if self.sender_thread:
            self.sender_thread.pause()
            self.pause_btn.setText("Resume")
            self.pause_btn.clicked.disconnect()
            self.pause_btn.clicked.connect(self.resume_sending)
    
    def resume_sending(self):
        if self.sender_thread:
            self.sender_thread.resume()
            self.pause_btn.setText("Pause")
            self.pause_btn.clicked.disconnect()
            self.pause_btn.clicked.connect(self.pause_sending)
    
    def stop_sending(self):
        if self.sender_thread:
            self.sender_thread.stop()
            self.sender_thread.wait()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        self.status_log.append(message)
    
    def sending_finished(self, success, count):
        self.send_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        self.summary_label.setText(f"✓ Sent {count} emails this session")
        QMessageBox.information(self, "Complete", f"Sent {count} emails successfully")
        self._update_recipients_table()
        self.refresh_logs()
    
    def refresh_logs(self):
        self.logs_table.setRowCount(0)
        if os.path.exists(SENT_LOG):
            with open(SENT_LOG, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in list(reader)[:100]:  # Show last 100
                    if len(row) >= 2:
                        self.logs_table.insertRow(0)
                        self.logs_table.setItem(0, 0, QTableWidgetItem(row[0]))
                        self.logs_table.setItem(0, 1, QTableWidgetItem(row[1]))
    
    def clear_logs(self):
        reply = QMessageBox.question(self, "Confirm", "Clear all sent logs?")
        if reply == QMessageBox.Yes:
            if os.path.exists(SENT_LOG):
                os.remove(SENT_LOG)
            self.refresh_logs()
            QMessageBox.information(self, "Success", "Logs cleared")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmailSenderGUI()
    window.show()
    sys.exit(app.exec_())
