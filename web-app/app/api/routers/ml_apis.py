from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import joblib
import pandas as pd
import numpy as np 
import os
import sys

router = APIRouter()

# Setup templates and static files
templates = Jinja2Templates(directory="templates")

# Define the path to artifacts relative to the project root
# NOTE: Ensure the directory structure (app/ml_artifacts) is correctly accessible from where FastAPI is run
ARTIFACTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'ml_artifacts')

# Load ML components once at startup
ML_PIPELINE = None
ML_METRICS = {'accuracy': 0.0, 'report': 'N/A', 'feature_names': []}
ML_IMPORTANCE = pd.DataFrame()

try:
    # Adjust paths based on the expected location of the artifacts
    pipeline_path = os.path.join(ARTIFACTS_PATH, '..\..\ml_artifacts\ml_model_pipeline.pkl')
    metrics_path = os.path.join(ARTIFACTS_PATH, '..\..\ml_artifacts\ml_metrics.pkl')
    importance_path = os.path.join(ARTIFACTS_PATH, '..\..\ml_artifacts\ml_feature_importance.pkl')
    
    ML_PIPELINE = joblib.load(pipeline_path)
    ML_METRICS.update(joblib.load(metrics_path))
    ML_IMPORTANCE = joblib.load(importance_path)
    
    # Ensure importance is sorted for UI display
    if not ML_IMPORTANCE.empty:
        ML_IMPORTANCE = ML_IMPORTANCE.sort_values(by='importance', ascending=False).head(5)

except FileNotFoundError:
    print(f"WARNING: ML model files not found in {ARTIFACTS_PATH}. Please run train_model.py first.")
    # Keep the default empty/safe values

# --- 2. /predict Endpoint (GET for Form) ---
@router.get("/predict", response_class=HTMLResponse)
async def predict_page(request: Request):
    """Renders the prediction form page with model performance metrics."""
    context = {
        "request": request,
        "features": ML_METRICS.get('feature_names', []),
        "title": "Predict Student Grade",
        # Ensure 'importance' is passed as a list of dicts for Jinja2
        "importance": ML_IMPORTANCE.to_dict('records'),
        "accuracy": f"{ML_METRICS.get('accuracy', 0.0) * 100:.2f}%"
    }
    return templates.TemplateResponse(
        "pages/predict.html", context)

@router.get("/visuals", response_class=HTMLResponse)
async def predict_page(request: Request):
    """Renders the prediction form page with model performance metrics."""
    context = {
        "request": request,
        "title": "Analytical Data Exploration: Student Performance"
    }
    return templates.TemplateResponse(
        "pages/visuals.html", context)

# --- 3. /predict Endpoint (POST for Prediction) ---
@router.post("/predict")
async def make_prediction(
    # NOTE: ALL 13 NEW FIELDS MUST BE INCLUDED HERE
    Student_Age: str = Form(...),
    Sex: str = Form(...),
    High_School_Type: str = Form(...),
    Scholarship: str = Form(...), # Now categorical/numerical value
    Additional_Work: str = Form(...),
    Sports_activity: str = Form(...),
    Transportation: str = Form(...),
    Weekly_Study_Hours: str = Form(...),
    Attendance: str = Form(...),
    Reading: str = Form(...),
    Notes: str = Form(...),
    Listening_in_Class: str = Form(...),
    Project_work: str = Form(...)
):
    """Processes form data and returns a grade prediction and recommendation."""
    if ML_PIPELINE is None:
        return {"error": "Model not loaded. Please ensure ML artifacts exist and are accessible."}, 500
    
    try:
        # 1. Create a DataFrame from the form inputs
        input_data = pd.DataFrame([{
            'Student_Age': int(Student_Age),
            'Sex': Sex,
            'High_School_Type': High_School_Type,
            'Scholarship': int(Scholarship), # Converted to int
            'Additional_Work': Additional_Work,
            'Sports_activity': Sports_activity,
            'Transportation': Transportation,
            'Weekly_Study_Hours': int(Weekly_Study_Hours),
            'Attendance': Attendance,
            'Reading': Reading,
            'Notes': Notes,
            'Listening_in_Class': Listening_in_Class,
            'Project_work': Project_work
        }])
        
        # 2. Get prediction
        predicted_grade_encoded = ML_PIPELINE.predict(input_data)[0]
        
        # 3. Get probability 
        predicted_proba = ML_PIPELINE.predict_proba(input_data).max()
        
    except Exception as e:
        # Catch errors during conversion or prediction
        return {"error": f"Prediction failed due to processing error: {e}"}, 500

    
    # 4. Generate Recommendation
    recommendation = "Review the top features affecting performance and see where you can improve your input profile."
    
    # Helper to clean up feature name for display
    def clean_feature_name(feature_name):
        return feature_name.replace('onehot__', '').replace('_', ' ').title()

    top_feature_row = ML_IMPORTANCE.iloc[0] if not ML_IMPORTANCE.empty else None
    
    if predicted_grade_encoded in ['A', 'B']:
        recommendation = "Excellent work! Your current profile strongly indicates success. To maintain this, ensure your <b>Weekly Study Hours</b> remain consistent and high-impact activities like <b>Project Work</b> are prioritized."
    elif predicted_grade_encoded in ['C', 'D']:
        if top_feature_row is not None:
             top_feature_name = clean_feature_name(top_feature_row['feature'])
             recommendation = f"Good performance, but there is room for improvement. The analysis suggests that improving your focus on <b>{top_feature_name}</b> could boost your grade significantly."
        else:
             recommendation = "Good work, but consider increasing your Weekly Study Hours and ensuring consistent attendance to push for a higher grade."
    elif predicted_grade_encoded in ['E', 'Fail']:
        if top_feature_row is not None and top_feature_row['feature'] in ['Weekly_Study_Hours', 'Attendance']:
            top_feature_name = clean_feature_name(top_feature_row['feature'])
            recommendation = f"Your predicted grade suggests a high risk. We recommend urgent focus on <b>{top_feature_name}</b> and re-evaluating your learning methods (Notes, Listening). Every small improvement here will help."
        else:
            recommendation = "Your predicted grade suggests a high risk. Focus immediately on improving your <b>Attendance</b> and increasing your <b>Weekly Study Hours</b>."


    return {
        "predicted_grade": predicted_grade_encoded,
        "recommendation": recommendation,
        "confidence": f"{predicted_proba * 100:.2f}%"
    }