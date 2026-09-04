from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from database.db import Base


class Email(Base):
    """Stores every email and its AI analysis."""

    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, nullable=False)  # Gmail's unique ID
    sender_email = Column(String, nullable=False)
    sender_name = Column(String)
    subject = Column(String)
    body_text = Column(Text)
    received_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, server_default=func.now())

    # AI Analysis
    category = Column(String)  # support, sales, spam, etc.
    priority = Column(String)  # low, medium, high, urgent
    extracted_info = Column(JSON)  # structured facts from AI
    suggested_reply = Column(Text)
    kb_used = Column(Boolean, default=False)

    # Response
    reply_sent = Column(Boolean, default=False)
    reply_sent_at = Column(DateTime)
    reply_body = Column(Text)

    # Status
    status = Column(String, default="processed")  # processed, failed, skipped


class Log(Base):
    """Stores events that happen to each email."""

    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    event = Column(String, nullable=False)  # e.g. "email_fetched", "reply_sent"
    detail = Column(Text)
    created_at = Column(DateTime, server_default=func.now())