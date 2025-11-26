import pandas as pd
import numpy as np

# --- 1. Define the parameters for data generation ---
N_ROWS = 1000

# Define choices for categorical variables
CHOICES = {
    'Student_Age': np.arange(18, 25),
    'Sex': ['Male', 'Female'],
    'High_School_Type': ['State', 'Private', 'Other'],
    # Scholarship is now a percentage from a choice of values
    'Scholarship': [0, 25, 50, 75, 100], 
    'Additional_Work': ['Yes', 'No'],
    'Sports_activity': ['Yes', 'No'],
    'Transportation': ['Private', 'Bus', 'Other'],
    'Weekly_Study_Hours': np.arange(0, 11),  # 0 to 10 hours
    'Attendance': ['Always', 'Sometimes', 'Never'],
    'Reading': ['Yes', 'No'],
    'Notes': ['Yes', 'No'],
    'Listening_in_Class': ['Yes', 'No'],
    'Project_work': ['Yes', 'No'],
    # CORRECTED: Added comma between 'E' and 'Fail'
    'Grade': ['A', 'B', 'C', 'D', 'E', 'Fail'] 
}

# Define the probability weights for a more realistic distribution
PROBABILITIES = {
    'Sex': [0.55, 0.45],
    'High_School_Type': [0.40, 0.35, 0.25],
    'Scholarship': [0.40, 0.15, 0.25, 0.10, 0.10], # Probabilities for [0, 25, 50, 75, 100]
    'Additional_Work': [0.40, 0.60],
    'Sports_activity': [0.25, 0.75],
    'Transportation': [0.45, 0.35, 0.20],
    'Attendance': [0.40, 0.35, 0.25],
    'Notes': [0.65, 0.35],
    'Listening_in_Class': [0.60, 0.40],
    'Project_work': [0.80, 0.20],
    # CORRECTED: Probabilities for ['A', 'B', 'C', 'D', 'E', 'Fail'] summing to 1.00
    'Grade': [0.10, 0.20, 0.30, 0.15, 0.10, 0.15] 
}

# --- 2. Initialize the DataFrame ---
data = pd.DataFrame()

# --- 3. Generate columns with defined distributions ---
for col, choices in CHOICES.items():
    if col in PROBABILITIES:
        # Use weighted random choice for categorical and discrete numerical data (like Scholarship)
        data[col] = np.random.choice(choices, size=N_ROWS, p=PROBABILITIES[col])
    else:
        # Use uniform random choice (for Age, Study Hours)
        data[col] = np.random.choice(choices, size=N_ROWS)

# --- 4. Introduce Conditional Logic (Making the data 'Smart') ---

# Identify students who are likely to fail (low study, bad attendance, no project)
low_perform_mask = (data['Weekly_Study_Hours'] <= 2) & \
                   (data['Attendance'].isin(['Sometimes', 'Never'])) & \
                   (data['Project_work'] == 'No')

# Adjust the 'Grade' for these students to be mostly 'D', 'E' or 'Fail'
# CORRECTED: Updated choices and probabilities to reflect the new D/E/Fail grades
data.loc[low_perform_mask, 'Grade'] = np.random.choice(
    ['D', 'E', 'Fail'], size=low_perform_mask.sum(), p=[0.2, 0.3, 0.5]
)

# Identify students who are likely to get an 'A' (high study, always attendance, reading)
high_perform_mask = (data['Weekly_Study_Hours'] >= 7) & \
                    (data['Attendance'] == 'Always') & \
                    (data['Reading'] == 'Yes')

# Adjust the 'Grade' for these students to be mostly 'A' or 'B'
# CORRECTED: Adjusted weights slightly but kept focus on A/B
data.loc[high_perform_mask, 'Grade'] = np.random.choice(
    ['A', 'B', 'C'], size=high_perform_mask.sum(), p=[0.6, 0.3, 0.1]
)

# --- 5. Export to CSV ---
output_filename = 'DataSets/student_performance_dummy_data_1000.csv'
data.to_csv(output_filename, index=False)

print(f"Successfully generated {N_ROWS} rows of dummy data.")
print(f"Data saved to {output_filename}")
print("\nFirst 5 rows of the generated data:")
print(data.head())