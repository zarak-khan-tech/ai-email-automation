import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime


def decode_str(s):
    """Decodes weird email text into normal readable text."""
    if s is None:
        return ""
    decoded, charset = decode_header(s)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(charset or "utf-8", errors="ignore")
    return str(decoded)


def get_email_body(msg):
    """Extracts the plain text body from an email message."""
    body = ""

    if msg.is_multipart():
        # Email has multiple parts (text, attachments, etc.)
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            # Get plain text
            if content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
                except:
                    pass

            # Fallback: get HTML if no plain text
            if content_type == "text/html" and not body:
                try:
                    html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    # Simple HTML to text (remove tags)
                    import re
                    body = re.sub(r"<[^>]+>", "", html)
                    body = re.sub(r"\s+", " ", body).strip()
                except:
                    pass
    else:
        # Simple email with just text
        try:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        except:
            body = str(msg.get_payload())

    return body.strip()


def parse_email(raw_email_bytes):
    """Takes raw email bytes from Gmail and returns clean data."""
    msg = email.message_from_bytes(raw_email_bytes)

    # Extract fields
    message_id = msg.get("Message-ID", "")
    subject = decode_str(msg.get("Subject", ""))
    from_header = decode_str(msg.get("From", ""))
    date_header = msg.get("Date")

    # Parse sender name and email
    # Format: "John Doe" <john@example.com> OR just john@example.com
    if "<" in from_header and ">" in from_header:
        sender_name = from_header.split("<")[0].strip().strip('"')
        sender_email = from_header.split("<")[1].split(">")[0].strip()
    else:
        sender_name = ""
        sender_email = from_header.strip()

    # Parse date
    try:
        received_at = parsedate_to_datetime(date_header)
    except:
        received_at = datetime.now()

    # Get body
    body_text = get_email_body(msg)

    return {
        "message_id": message_id,
        "sender_email": sender_email,
        "sender_name": sender_name,
        "subject": subject,
        "body_text": body_text,
        "received_at": received_at,
    }