import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

# Load the generated dummy data
data = pd.read_csv('DataSets/student_performance_realistic_200.csv')

# --- 1. Define Features (X) and Target (y) ---
# Target variable is 'Grade'
X = data.drop('Grade', axis=1)
y = data['Grade']

# --- 2. Define Preprocessing Steps ---
# Identify columns by their data type/handling
categorical_features = [col for col in X.columns if X[col].dtype == 'object']
numerical_features = [col for col in X.columns if X[col].dtype != 'object']
# Note: 'Student_Age' and 'Weekly_Study_Hours' are already integer, we can treat them as-is.

# Create a preprocessor using ColumnTransformer
preprocessor = ColumnTransformer(
    transformers=[
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features),
        # 'passthrough' leaves numerical columns as they are
        ('num_pass', 'passthrough', numerical_features)
    ],
    remainder='drop' # Drop any other columns not specified
)

# --- 3. Create the ML Pipeline ---
# Using RandomForestClassifier, a great general-purpose classifier
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'))
])

# --- 4. Split Data and Train ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print("--- Training Model... ---")
model.fit(X_train, y_train)
print("--- Training Complete. ---")

# --- 5. Evaluate Model ---
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred, zero_division=0)
conf_mat = confusion_matrix(y_test, y_pred)

print(f"\nModel Accuracy on Test Set: {accuracy:.4f}")
print("\nClassification Report:\n", report)

# --- 6. Save the Trained Model and Evaluation Metrics ---
# Save the entire pipeline (preprocessor + model)
joblib.dump(model, 'ml_model_pipeline.pkl')
print("\n✅ Model pipeline saved as ml_model_pipeline.pkl")

# Save evaluation metrics for the /predict page explanation
metrics = {
    'accuracy': accuracy,
    'report': report,
    'confusion_matrix': conf_mat.tolist(),
    'target_names': list(y.unique()),
    'feature_names': list(X.columns)
}
joblib.dump(metrics, 'ml_metrics.pkl')
print("✅ Model metrics saved as ml_metrics.pkl")

# --- Bonus: Get Feature Importance from the trained model ---
# This is crucial for your 'study plan design' explanation!
feature_importances = model.named_steps['classifier'].feature_importances_
# Get the names of the one-hot encoded features
encoded_feature_names = model.named_steps['preprocessor'].get_feature_names_out()

importance_df = pd.DataFrame({
    'feature': encoded_feature_names,
    'importance': feature_importances
}).sort_values(by='importance', ascending=False).head(10)

print("\nTop 10 Feature Importances (for Study Plan Design):\n")
print(importance_df)
# Save importance for visual in /predict
joblib.dump(importance_df, 'ml_feature_importance.pkl')