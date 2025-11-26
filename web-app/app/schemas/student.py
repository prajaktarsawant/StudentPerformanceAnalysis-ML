from pydantic import BaseModel, Field
from typing import Optional

# List of all columns for the API/UI interaction
class StudentDataCreate(BaseModel):
    # Student_ID is typically auto-generated, but kept as required for CSV matching
    # Student_ID: Optional[int] = Field(..., description="Unique ID for the student.") 
    Student_Age: int
    Sex: str # 'Male', 'Female', 'Other'
    High_School_Type: str
    Scholarship: int # '50%', '100%', 'No'
    Additional_Work: str # 'Yes', 'No'
    Sports_activity: str # 'Yes', 'No'
    Transportation: str # 'Private', 'Bus'
    Weekly_Study_Hours: float # Use float for robustness
    Attendance: str # 'Always', 'Sometimes', 'Never'
    Reading: str # 'Yes', 'No'
    Notes: str
    Listening_in_Class: str
    Project_work: str
    Grade: Optional[str] = None 

# Used when reading data from the database (output)
class StudentDataInDB(StudentDataCreate):
    class Config:
        from_attributes = True