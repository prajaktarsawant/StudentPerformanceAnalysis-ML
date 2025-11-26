from sqlalchemy import Column, Integer, String, Float
from ..core.database import Base

class StudentData(Base):
    __tablename__ = "student_performance_records"

    # Primary Key and Identifiers
    Student_ID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    Student_Age = Column(Integer, nullable=False) # Changed to String to hold '19-22'

    # Categorical Features (Most are Strings now)
    Sex = Column(String, nullable=False)        # e.g., 'Male', 'Female'
    High_School_Type = Column(String, nullable=False)
    Scholarship = Column(Integer, nullable=False) # e.g., '50', '100'
    Additional_Work = Column(String, default="No")
    Sports_activity = Column(String, default="No")
    Transportation = Column(String, nullable=False)
    
    # Quantitative/Ordinal Features
    Weekly_Study_Hours = Column(Float, nullable=False) # Changed to Float just in case
    Attendance = Column(String, nullable=False) # e.g., 'Always', 'Sometimes'
    
    # Learning Style/Engagement (Categorical/Ordinal)
    Reading = Column(String, nullable=False) # e.g., 'Yes', 'No'
    Notes = Column(String, nullable=False) 
    Listening_in_Class = Column(String, nullable=False)
    Project_work = Column(String, nullable=False)

    # Target Variable
    Grade = Column(String, index=True) # e.g., 'AA', 'A', 'B', etc.
    
    def __repr__(self):
        return f"<Student(ID={self.Student_ID}, Grade={self.Grade})>"