from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .core.database import engine, Base
from .models import item as item_model  # Import models to register them
from .models import student as student_model  # Import models to register them
from .models import data_entry_email as data_entry_email_model  # Import models to register them

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Modular App")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 templates (Template configuration remains here)
templates = Jinja2Templates(directory="templates")

# --- Include Routers ---
from .api.routers import ui

app.include_router(ui.router)
# If you add API endpoints, include them like this:
from .api.routers import item, student
app.include_router(student.router, prefix="/api/v1")
app.include_router(item.router, prefix="/api/v1", tags=["items"])