from fastapi import Query, APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, Response, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...crud import crud_item
from ...crud import crud_student
from ...schemas.item import ItemCreate
from io import StringIO
import csv
import pandas as pd
from ...schemas.student import StudentDataCreate, StudentDataInDB
from starlette.status import HTTP_303_SEE_OTHER
from ...crud.data_entry_email import log_email_invitation, get_email_logs
import requests
import json

EXPECTED_HEADERS = [
    'Student_Age', 'Sex', 'High_School_Type', 'Scholarship', 
    'Additional_Work', 'Sports_activity', 'Transportation', 
    'Weekly_Study_Hours', 'Attendance', 'Reading', 'Notes', 
    'Listening_in_Class', 'Project_work', 'Grade'
]

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    tags=["UI Rendering"],
    include_in_schema=False # Optional: hide UI routes from the OpenAPI docs
)

# Helper function to get the schema details
from ...models.student import StudentData
def get_dataset_schema():
    """Dynamically generates schema information from the SQLAlchemy model."""
    schema = []
    # Ensure StudentModel is imported and accessible
    for col in StudentData.__table__.columns:
        schema.append({
            "name": col.name,
            "type": str(col.type),
            "nullable": col.nullable,
            "pk": col.primary_key,
            "description": f"Student {col.name.replace('_', ' ')}."
        })
    return schema

@router.get("/", response_class=HTMLResponse, name="home")
async def dashboard_view(request: Request, db: Session = Depends(get_db)):
    # 1. Calculate Metrics
    data_quality_metrics = crud_student.calculate_data_quality_metrics(db) 
    
    # 2. Get Schema Data
    schema_data = get_dataset_schema()
    
    return templates.TemplateResponse(
        "pages/index.html",
        {
            "request": request,
            "title": "Dashboard & Data Quality",
            "metrics": data_quality_metrics,
            "schema": schema_data  # Pass the schema data
        }
    )

@router.post("/create/")
async def create_item_ui(
    name: str = Form(...), 
    description: str = Form(None), 
    db: Session = Depends(get_db)
):
    """Handles item creation from a submitted form and redirects."""
    item_in = ItemCreate(name=name, description=description)
    crud_item.create_item(db, item_in=item_in)
    
    # Redirect back to the home page (Standard web pattern after POST)
    return RedirectResponse(url="/", status_code=303)



@router.get("/data", tags=["UI Rendering"])
def view_data_table(request: Request, db: Session = Depends(get_db)):
    """Renders the page to view all student data records."""
    
    # Fetch data using the CRUD function
    students = crud_student.get_students(db, limit=500) # Limit to 50 records for display
    
    return templates.TemplateResponse(
        "pages/student_data_table.html", 
        {"request": request, "title": "Student Performance Data", "students": students}
    )

@router.get("/data/import", tags=["UI Rendering"])
def import_data_page(request: Request):
    """Renders the file upload form page."""
    return templates.TemplateResponse(
        "pages/data_import.html", 
        {"request": request, "title": "Bulk Data Import"}
    )

@router.get("/data/download_template", tags=["UI Rendering"])
def download_template():
    """Serves the CSV file with correct headers."""
    
    # Create the CSV content in memory
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(EXPECTED_HEADERS)
    
    csv_content = output.getvalue()
    
    # Return as a FileResponse
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=import_template_header.csv"
        }
    )

@router.post("/data/upload", tags=["Data Import"])
async def upload_and_import_data(
    request: Request,
    csv_file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # Ensure the file is a CSV
    if not csv_file.filename.endswith('.csv'):
        return templates.TemplateResponse(
            "pages/data_import.html", 
            {"request": request, "title": "Bulk Data Import", "error": "Invalid file type. Please upload a .csv file."}
        )

    content = await csv_file.read()
    csv_data = StringIO(content.decode("utf-8"))
    
    # Use pandas to easily load and inspect headers
    try:
        df = pd.read_csv(csv_data)
    except Exception as e:
        return templates.TemplateResponse(
            "pages/data_import.html", 
            {"request": request, "title": "Bulk Data Import", "error": f"Error reading CSV: {e}"}
        )

    # 1. HEADER VALIDATION
    uploaded_headers = list(df.columns)
    if uploaded_headers != EXPECTED_HEADERS:
        missing = [h for h in EXPECTED_HEADERS if h not in uploaded_headers]
        extra = [h for h in uploaded_headers if h not in EXPECTED_HEADERS]
        
        error_msg = f"Header mismatch. Missing columns: {missing}. Extra columns found: {extra}."
        
        return templates.TemplateResponse(
            "pages/data_import.html", 
            {"request": request, "title": "Bulk Data Import", "error": error_msg}
        )

    # 2. DATA LOADING AND Pydantic VALIDATION (Crucial Step)
    imported_count = 0
    errors = []
    
    for index, row in df.iterrows():
        try:
            # Create a Pydantic model instance for row validation
            # .to_dict() converts the pandas series (row) to a dict
            student_data = StudentDataCreate(**row.to_dict()) 
            
            # If validation succeeds, load data into the database
            crud_student.create_student_record(db=db, record=student_data)
            imported_count += 1
        except Exception as e:
            # Log specific validation or DB error for that row
            errors.append(f"Row {index + 2} (ID: {row.get('Student_ID', 'N/A')}): {e}")

    if errors:
         return templates.TemplateResponse(
            "pages/data_import.html", 
            {"request": request, "title": "Bulk Data Import", "imported_count": imported_count, "errors": errors}
        )
        
    # 3. SUCCESS REDIRECT
    # Use HTTP_303_SEE_OTHER (303) status code for Post/Redirect/Get pattern
    # Prevents form resubmission on refresh
    response = RedirectResponse(url="/data?success=True", status_code=HTTP_303_SEE_OTHER)
    return response

@router.get("/data/add", response_class=HTMLResponse, name="add_student_form")
async def add_student_form(request: Request):
    return templates.TemplateResponse(
        "pages/student_add_form.html",
        {"request": request, "title": "Add New Student Record"}
    )

@router.post("/data/add", response_class=RedirectResponse, name="submit_student_record")
async def submit_student_record_view(    
    # Identification and Demographics
    #student_id: str = Form(..., alias="student_id"),
    is_invitee: bool = Form(False, alias="is_invitee"),
    student_age: str = Form(..., alias="student_age"),
    sex: str = Form(..., alias="sex"),
    high_school_type: str = Form(..., alias="high_school_type"),
    scholarship: str = Form(..., alias="scholarship"),
    
    # Extracurricular and Logistics
    additional_work: str = Form(..., alias="additional_work"),
    sports_activity: str = Form(..., alias="sports_activity"),
    transportation: str = Form(..., alias="transportation"),
    
    # Performance Metrics
    weekly_study_hours: float = Form(..., alias="weekly_study_hours"), # Must be cast to float/int
    attendance: str = Form(..., alias="attendance"),
    final_grade: str = Form(..., alias="final_grade"),
    
    # Study Habits (Yes/No fields)
    reading: str = Form(..., alias="reading"),
    notes: str = Form(..., alias="notes"),
    listening_in_class: str = Form(..., alias="listening_in_class"),
    project_work: str = Form(..., alias="project_work"),
    
    # Dependency Injection
    db: Session = Depends(get_db)
):
    try:
        student_data = StudentDataCreate(
            #Student_ID=student_id,
            Student_Age=student_age,
            Sex=sex,
            High_School_Type=high_school_type,
            Scholarship=scholarship,
            Additional_Work=additional_work,
            Sports_activity=sports_activity,
            Transportation=transportation,
            Weekly_Study_Hours=weekly_study_hours, 
            
            Attendance=attendance,
            Grade=final_grade,
            Reading=reading,
            Notes=notes,
            Listening_in_Class=listening_in_class,
            Project_work=project_work
        )
    except Exception as e:
        print(f"Validation Error: {e}")
        return RedirectResponse(url="/data/add", status_code=303)


    # 2. Save data into the database using CRUD
    crud_student.create_student_record(db=db, record=student_data)
    
    # 3. Redirect back to the data table on success
    if is_invitee:
        return RedirectResponse(url="/data/invitee?invitee_success=True", status_code=303)
    return RedirectResponse(url="/data", status_code=303)

async def send_email(recipient: str, form_link: str):
    url = "https://n8n.prasadsawant.com/webhook/send-data-collection-invite-email"

    payload = json.dumps({
        "email": recipient,
        "link": form_link
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code >= 200 and response.status_code < 300:
        try:
            response_data = response.json()
            print(f"Request Status Code: {response.status_code}")
            print(f"Response Data: {response_data}")
            return True
        
        except json.JSONDecodeError:
            print("Error: Could not decode response as JSON.")
            return False
    else:
        # Handle non-successful HTTP status codes
        print(f"Error: Request failed with status code {response.status_code}")
        # You can return the response text or status code for debugging
        return False

# --- GET Route: Displays the Email Log table ---
@router.get("/email_log", response_class=HTMLResponse, name="email_log")
async def email_log_view(request: Request, db: Session = Depends(get_db)):
    """Displays the log of sent email invitations by fetching data from the DB."""
    
    logs = get_email_logs(db) # Use the CRUD function
    
    return templates.TemplateResponse(
        "pages/email_log_table.html",
        {"request": request, "title": "Invitation Log", "logs": logs}
    )

# --- POST Route: Handles email sending and logging ---
@router.post("/send_invitations", name="send_invitations")
async def send_invitations_view(
    request: Request,
    db: Session = Depends(get_db),
    email_list: str = Form(...),
):
    emails = [e.strip() for e in email_list.split(',') if e.strip()]
    sent_count = 0

    for email in emails:
        form_link = str(request.base_url).rstrip('/') + f'/data/invitee/add?email={email}'

        success = await send_email(email, form_link)
        status = "SENT" if success else "FAILED"
        
        # Log the action using the CRUD function
        log_email_invitation(db, email, form_link, status)
        
        if success:
            sent_count += 1
            
    db.commit() # Commit all log entries together to the database

    return RedirectResponse(
        url="/data", 
        status_code=303,
        headers={"X-Alert": f"{sent_count} invitation(s) logged and sent successfully."}
    )

@router.get("/data/invitee/add", response_class=HTMLResponse, name="invitee_add_form")
async def invitee_add_form_view(
    request: Request, 
    email: str = Query(..., alias="email") # Captures the 'email' query parameter
):
    """
    Displays the simplified data entry form for an external invitee.
    The form link must be: http://127.0.0.1:8000/data/invitee/add?email=prasad@gmail.com
    """
    
    # Render the minimal template and pass the captured email ID
    return templates.TemplateResponse(
        "pages/invitee_add_form.html",
        {
            "request": request, 
            "title": "Invited Data Submission", 
            "email_id": email # Passed to the template to be used in the hidden field
        }
    )

@router.get("/data/invitee", response_class=HTMLResponse, name="invitee_feedback")
async def invitee_feedback_view(
    request: Request,
    invitee_success: bool = Query(False, alias="invitee_success")
):
    """
    Displays the submission feedback page (success or failure) to the invitee.
    Accessed via: /data/invitee?invitee_success=True
    """
    
    context = {
        "request": request,
        "title": "Submission Status",
        "success": invitee_success,
    }
    
    return templates.TemplateResponse(
        "pages/invitee_feedback.html",
        context
    )