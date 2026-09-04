import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.logger import get_logger

logger = get_logger()


class EmailSender:
    """Sends emails via Gmail SMTP."""

    def __init__(self, email_address, app_password):
        self.email_address = email_address
        self.app_password = app_password

    def send_reply(self, to_email, subject, reply_body, original_message_id=None):
        """Sends a reply email."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to_email
            msg["Subject"] = f"Re: {subject}"

            if original_message_id:
                msg["In-Reply-To"] = original_message_id
                msg["References"] = original_message_id

            msg.attach(MIMEText(reply_body, "plain", "utf-8"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.email_address, self.app_password)
                server.send_message(msg)

            logger.info(f"Reply sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            return False