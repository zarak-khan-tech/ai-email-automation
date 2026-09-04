import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings
from database.db import SessionLocal
from database.operations import check_duplicate, save_email, update_email, log_event
from email_handler.poller import EmailPoller
from email_handler.sender import EmailSender
from ai.classifier import classify_email
from ai.responder import generate_reply
from utils.logger import get_logger

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# ===== RENDER HEALTH CHECK (tiny built-in web server) =====
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Email Automation is Running')
    
    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()
# ============================================================

# ==================== SAFETY SWITCH ====================
# Set to False to STOP sending real emails
# Set to True only when you are 100% ready
SEND_REAL_EMAILS = False
# =======================================================

# Domains to skip (Facebook, LinkedIn, auto-notifications)
SKIP_DOMAINS = ["facebookmail.com", "linkedin.com", "twitter.com", "instagram.com", "noreply", "no-reply"]

logger = get_logger()


def process_emails():
    """Main function: fetches emails, analyzes them, replies, and saves everything."""
    
    db = SessionLocal()
    poller = EmailPoller(settings.GMAIL_ADDRESS, settings.GMAIL_APP_PASSWORD)
    sender = EmailSender(settings.GMAIL_ADDRESS, settings.GMAIL_APP_PASSWORD)

    try:
        # Step 1: Connect to Gmail
        if not poller.connect():
            logger.error("Could not connect to Gmail. Will retry next time.")
            return

        # Step 2: Fetch new emails
        emails = poller.fetch_unseen()
        if not emails:
            logger.info("No new emails to process.")
            poller.disconnect()
            return

        # Step 3: Process each email
        for email_data in emails:
            msg_id = email_data["message_id"]

            # Check if already processed
            if check_duplicate(db, msg_id):
                logger.info(f"Skipping duplicate email: {msg_id}")
                continue

            # Skip notification emails (Facebook, LinkedIn, etc.)
            sender_email_lower = email_data["sender_email"].lower()
            if any(domain in sender_email_lower for domain in SKIP_DOMAINS):
                logger.info(f"Skipping notification email from {email_data['sender_email']}")
                # Save to DB as skipped but don't process further
                db_email = save_email(db, {
                    "message_id": msg_id,
                    "sender_email": email_data["sender_email"],
                    "sender_name": email_data["sender_name"],
                    "subject": email_data["subject"],
                    "body_text": email_data["body_text"],
                    "received_at": email_data["received_at"],
                    "status": "skipped"
                })
                log_event(db, db_email.id, "skipped", "Notification email - auto skipped")
                continue

            logger.info(f"Processing email from {email_data['sender_email']} - {email_data['subject']}")

            # Save email to database first
            db_email = save_email(db, {
                "message_id": msg_id,
                "sender_email": email_data["sender_email"],
                "sender_name": email_data["sender_name"],
                "subject": email_data["subject"],
                "body_text": email_data["body_text"],
                "received_at": email_data["received_at"],
                "status": "processed"
            })

            log_event(db, db_email.id, "email_fetched", f"From: {email_data['sender_email']}")

            # Skip if body is empty
            if not email_data["body_text"].strip():
                logger.warning("Empty body, skipping.")
                update_email(db, db_email.id, {"status": "skipped"})
                log_event(db, db_email.id, "skipped", "Empty body")
                continue

            # Step 4: AI Classification
            try:
                ai_result = classify_email(
                    sender_name=email_data["sender_name"],
                    sender_email=email_data["sender_email"],
                    subject=email_data["subject"],
                    body=email_data["body_text"]
                )
                logger.info(f"AI classified as: {ai_result['category']} | Priority: {ai_result['priority']}")
                log_event(db, db_email.id, "ai_classified", f"Category: {ai_result['category']}, Priority: {ai_result['priority']}")
            except Exception as e:
                logger.error(f"AI classification failed: {e}")
                update_email(db, db_email.id, {"status": "failed"})
                log_event(db, db_email.id, "ai_failed", str(e))
                continue

            # Step 5: AI Reply Generation
            try:
                reply_text = generate_reply(
                    sender_name=email_data["sender_name"],
                    subject=email_data["subject"],
                    body=email_data["body_text"],
                    category=ai_result["category"],
                    priority=ai_result["priority"],
                    summary=ai_result["summary"],
                    sender_intent=ai_result["extracted_info"]["sender_intent"]
                )
                logger.info("AI reply generated successfully")
                log_event(db, db_email.id, "reply_generated", "Reply created by AI")
            except Exception as e:
                logger.error(f"AI reply generation failed: {e}")
                update_email(db, db_email.id, {"status": "failed"})
                log_event(db, db_email.id, "reply_failed", str(e))
                continue

            # Step 6: Update email with AI analysis
            update_email(db, db_email.id, {
                "category": ai_result["category"],
                "priority": ai_result["priority"],
                "extracted_info": ai_result["extracted_info"],
                "suggested_reply": reply_text,
                "kb_used": True
            })

            # Step 7: Send reply via SMTP (SAFETY CHECK)
            if not SEND_REAL_EMAILS:
                logger.info("🛡️ SAFETY MODE ON: Reply NOT sent")
                log_event(db, db_email.id, "reply_skipped_safety", "Safety mode is ON - no real emails sent")
                # Still save the reply to database for review
                update_email(db, db_email.id, {
                    "reply_body": reply_text
                })
            else:
                try:
                    sent = sender.send_reply(
                        to_email=email_data["sender_email"],
                        subject=email_data["subject"],
                        reply_body=reply_text,
                        original_message_id=msg_id
                    )

                    if sent:
                        update_email(db, db_email.id, {
                            "reply_sent": True,
                            "reply_body": reply_text
                        })
                        log_event(db, db_email.id, "reply_sent", f"Reply sent to {email_data['sender_email']}")
                    else:
                        log_event(db, db_email.id, "reply_send_failed", "SMTP returned False")

                except Exception as e:
                    logger.error(f"Failed to send reply: {e}")
                    log_event(db, db_email.id, "reply_send_failed", str(e))

            # Step 8: Mark email as read in Gmail
            poller.mark_as_read(msg_id)

        # Disconnect from Gmail
        poller.disconnect()
        logger.info("Email processing cycle complete.")

    except Exception as e:
        logger.error(f"Critical error in process_emails: {e}")
    finally:
        db.close()


def main():
    """Starts the scheduler to check emails every X seconds."""
    
    # Validate settings first
    missing = settings.validate()
    if missing:
        logger.error(f"Missing required settings: {', '.join(missing)}")
        print(f"❌ Missing settings in .env: {', '.join(missing)}")
        return

    print("=" * 50)
    print("🤖 Email Automation System Starting...")
    print(f"⏰ Checking emails every {settings.POLL_INTERVAL_SECONDS} seconds")
    print(f"📧 Gmail: {settings.GMAIL_ADDRESS}")
    print(f"🤖 AI Model: {settings.OPENROUTER_MODEL}")
    print(f"🛡️ Safety Mode: {'ON (no emails sent)' if not SEND_REAL_EMAILS else 'OFF (sending real emails!)'}")
    print("=" * 50)

    # Run once immediately
    process_emails()

    # Then schedule to run repeatedly
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        process_emails,
        trigger=IntervalTrigger(seconds=settings.POLL_INTERVAL_SECONDS),
        id="email_poll",
        name="Check and process emails",
        replace_existing=True
    )
    scheduler.start()

    print("✅ Scheduler started. Press CTRL+C to stop.")
    print("-" * 50)

    # Keep the program running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping scheduler...")
        scheduler.shutdown()
        print("👋 Goodbye!")


if __name__ == "__main__":
    main()