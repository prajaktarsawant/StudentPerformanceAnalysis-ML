# app/crud/data_entry_email.py

from sqlalchemy.orm import Session
from ..models.data_entry_email import EmailLog
import datetime
from typing import List

def log_email_invitation(db: Session, email: str, link: str, status: str = "SENT"):
    """
    Creates a new log entry in the database.
    Note: The caller of this function must commit the session (db.commit()).
    """
    db_log = EmailLog(
        recipient_email=email,
        form_link=link,
        status=status,
        send_time=datetime.datetime.utcnow()
    )
    db.add(db_log)
    return db_log

def get_email_logs(db: Session) -> List[EmailLog]:
    """Retrieves all email logs, ordered by newest first."""
    return db.query(EmailLog).order_by(EmailLog.send_time.desc()).all()