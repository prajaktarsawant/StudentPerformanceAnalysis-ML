from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud import crud_student

router = APIRouter(
    tags=["Student"],
    include_in_schema=True
)

@router.get("/student-data", include_in_schema=True)
def get_student_data(
    db: Session = Depends(get_db),
    limit: int = 100,  # <-- Defined as a function argument, with a default value
    offset: int = 0    # <-- Defined as a function argument, with a default value
):
    """Renders the page to view all student data records, with pagination support."""
    
    # Fetch data using the CRUD function, passing the limit and offset
    # Note: Use the function arguments (limit, offset) instead of a fixed number
    students = crud_student.get_students(db, limit=limit, offset=offset)
    
    return {
        "students": students,
        "limit": limit,
        "offset": offset
    }