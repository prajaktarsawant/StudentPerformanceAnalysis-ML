# app/schemas/data_entry_email.py

from pydantic import BaseModel
import datetime

class EmailLogDB(BaseModel):
    """Schema for reading data entry email logs from the database."""
    id: int
    recipient_email: str
    send_time: datetime.datetime
    status: str
    form_link: str
    
    class Config:
        # Enables conversion from SQLAlchemy objects to Pydantic objects
        from_attributes = True