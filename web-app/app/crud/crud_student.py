from sqlalchemy.orm import Session
from app.models.student import StudentData as StudentModel
from app.schemas.student import StudentDataCreate
from sqlalchemy import func, text
from typing import Dict, Any

def get_student(db: Session, student_id: int):
    return db.query(StudentModel).filter(StudentModel.Student_ID == student_id).first()

def get_students(db: Session, limit: int = 100, offset: int = 0):
    return db.query(StudentModel).offset(offset).limit(limit).all()

def create_student_record(db: Session, record: StudentDataCreate):
    # We use .model_dump() to convert the Pydantic model to a dictionary for SQLAlchemy
    db_student = StudentModel(**record.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def calculate_data_quality_metrics(db: Session) -> Dict[str, Any]:
    """
    Calculates various data quality and submission metrics from the StudentModel table.
    """
    
    # 1. Total Records and Uniqueness
    total_records = db.query(StudentModel).count()
    
    if total_records == 0:
        return {
            "total_records": 0,
            "completion_rate": 0,
            "unique_student_ids": 0,
            "missing_values": 0,
            "invitee_submissions": 0, # Added invitee_submissions
            "age_distribution": []
        }

    # Assuming Student_ID is the unique identifier
    unique_student_ids = db.query(StudentModel.Student_ID).distinct().count()

    # 2. Data Completeness (Missing Values)
    
    # REQUIRED STRING FIELDS (Check for NULL OR Empty String)
    REQUIRED_STRING_FIELDS = [        
        StudentModel.Student_Age,
        StudentModel.Sex,
        StudentModel.Scholarship,
        StudentModel.Grade
    ]
    
    # REQUIRED NUMERIC/FLOAT FIELDS (Check ONLY for NULL)
    REQUIRED_NUMERIC_FIELDS = [
        StudentModel.Weekly_Study_Hours 
    ]
    
    missing_values_count = 0
    
    # Check String Fields
    for field in REQUIRED_STRING_FIELDS:
        missing_count = db.query(StudentModel).filter(
            (field == None) 
        ).count()
        missing_values_count += missing_count
        
    # Check Numeric Fields (Avoid checking for field == '' which causes DataError)
    for field in REQUIRED_NUMERIC_FIELDS:
        missing_count = db.query(StudentModel).filter(
            field == None
        ).count()
        missing_values_count += missing_count


    # Total possible required data points
    total_required_fields = len(REQUIRED_STRING_FIELDS) + len(REQUIRED_NUMERIC_FIELDS)
    total_possible_data_points = total_records * total_required_fields
    
    # Calculate completion rate
    if total_possible_data_points > 0:
        filled_data_points = total_possible_data_points - missing_values_count
        completion_rate = round((filled_data_points / total_possible_data_points) * 100, 1)
    else:
        completion_rate = 0

    
    # 3. Submission Source (Invitee Count)
    # ASSUMPTION: StudentModel has a 'is_invitee' Boolean column.
    try:
        invitee_submissions = db.query(StudentModel).filter(
            StudentModel.is_invitee == True
        ).count()
    except AttributeError:
        # Fallback if the 'is_invitee' column is missing from the model
        invitee_submissions = 0


    # 4. Age Distribution
    # FIX APPLIED: Order by the aggregate function object itself (.desc())
    age_distribution_results = db.query(
        StudentModel.Student_Age, 
        func.count(StudentModel.Student_Age)
    ).group_by(StudentModel.Student_Age).order_by(
        func.count(StudentModel.Student_Age).desc()
    ).all()
    
    # Convert results to a list of tuples: [('19-22', 80), ('23-26', 40), ...]
    age_distribution_list = [(age, count) for age, count in age_distribution_results]


    # 5. Compile and return the final dictionary
    return {
        "total_records": total_records,
        "completion_rate": completion_rate,
        "unique_student_ids": unique_student_ids,
        "missing_values": missing_values_count,
        "invitee_submissions": invitee_submissions, # Added back
        "age_distribution": age_distribution_list
    }

