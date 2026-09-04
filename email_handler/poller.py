import imaplib
from email_handler.parser import parse_email
from utils.logger import get_logger

logger = get_logger()


class EmailPoller:
    """Connects to Gmail IMAP and fetches unseen emails."""

    def __init__(self, email_address, app_password):
        self.email_address = email_address
        self.app_password = app_password
        self.mail = None

    def connect(self):
        """Connects to Gmail IMAP server."""
        try:
            self.mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            self.mail.login(self.email_address, self.app_password)
            self.mail.select("inbox")
            logger.info("Connected to Gmail IMAP successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Gmail IMAP: {e}")
            return False

    def fetch_unseen(self):
        """Fetches all unseen emails and returns list of parsed emails."""
        emails = []

        if not self.mail:
            logger.error("Not connected to IMAP")
            return emails

        try:
            # Search for UNSEEN emails
            status, messages = self.mail.search(None, "UNSEEN")

            if status != "OK" or not messages[0]:
                logger.info("No new emails found")
                return emails

            # messages[0] is a space-separated string of email IDs
            email_ids = messages[0].split()

            logger.info(f"Found {len(email_ids)} new email(s)")

            # Safety limit: only process 10 emails per run
            for email_id in email_ids[:10]:
                status, msg_data = self.mail.fetch(email_id, "(RFC822)")

                if status != "OK":
                    logger.warning(f"Failed to fetch email ID {email_id}")
                    continue

                # msg_data[0][1] contains the raw email bytes
                raw_email = msg_data[0][1]
                parsed = parse_email(raw_email)

                # Mark as read (optional - we do this after processing)
                # self.mail.store(email_id, '+FLAGS', '\\Seen')

                emails.append(parsed)

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")

        return emails

    def mark_as_read(self, message_id):
        """Marks a specific email as read by searching for its Message-ID."""
        try:
            status, messages = self.mail.search(None, f'HEADER Message-ID "{message_id}"')
            if status == "OK" and messages[0]:
                for email_id in messages[0].split():
                    self.mail.store(email_id, "+FLAGS", "\\Seen")
                    logger.info(f"Marked email {message_id} as read")
        except Exception as e:
            logger.error(f"Failed to mark email as read: {e}")

    def disconnect(self):
        """Closes the IMAP connection."""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                logger.info("Disconnected from Gmail IMAP")
            except:
                pass