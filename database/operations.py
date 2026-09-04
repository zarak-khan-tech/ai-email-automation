from sqlalchemy.orm import Session
from database.models import Email, Log


def check_duplicate(db: Session, message_id: str) -> bool:
    """Returns True if this email was already processed."""
    return db.query(Email).filter(Email.message_id == message_id).first() is not None


def save_email(db: Session, email_data: dict) -> Email:
    """Saves a new email to the database."""
    email = Email(**email_data)
    db.add(email)
    db.commit()
    db.refresh(email)
    return email


def update_email(db: Session, email_id: int, updates: dict) -> None:
    """Updates an existing email (e.g. after sending reply)."""
    db.query(Email).filter(Email.id == email_id).update(updates)
    db.commit()


def log_event(db: Session, email_id: int, event: str, detail: str = "") -> None:
    """Saves a log entry for what happened to an email."""
    log = Log(email_id=email_id, event=event, detail=detail)
    db.add(log)
    db.commit()