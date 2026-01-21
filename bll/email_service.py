import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

# 👇 ОНОВЛЕНО: Імпортуємо налаштування замість dotenv
import config 

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        # 👇 Беремо дані з файлу config.py
        self.email_address = config.EMAIL_SENDER
        self.email_password = config.EMAIL_PASSWORD
        self.sender_name = "Auth System" 

    def _send_thread(self, to_email: str, subject: str, body: str):
        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr((self.sender_name, self.email_address))
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html', 'utf-8'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
                
            print(f"[INFO] Email successfully sent to {to_email}")
            
        except Exception as e:
            print(f"[ERROR] Failed to send email to {to_email}: {str(e)}")

    def send_email_background(self, to_email: str, subject: str, body: str):
        email_thread = threading.Thread(
            target=self._send_thread,
            args=(to_email, subject, body)
        )
        email_thread.start()