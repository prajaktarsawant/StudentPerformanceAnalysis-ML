from sqlalchemy import Column, Integer, String, DateTime
from ..core.database import Base
import datetime

class EmailLog(Base):
    """Model for storing the history of invitation emails sent."""
    __tablename__ = "email_invitation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String, index=True, nullable=False)
    send_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    status = Column(String, default="SENT", nullable=False) # SENT or FAILED
    form_link = Column(String, nullable=False)