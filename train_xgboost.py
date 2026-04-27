import pandas as pd
import joblib
from xgboost import XGBClassifier

print("Loading data...")
df = pd.read_csv('student_data.csv')

# --- FEATURE ENGINEERING ---
# Safe fallback just in case 'cgpa_sem_1' isn't in your CSV yet
if 'cgpa_sem_1' not in df.columns:
    df['cgpa_sem_1'] = df['previous_cgpa'] 

# Calculate the 3 new Smart Features
df['momentum'] = df['previous_cgpa'] - df['cgpa_sem_1']
df['effort_score'] = (df['internal_marks'] + df['unit_test_marks']) / (df['study_hours_weekly'] + 1)
df['engagement_index'] = (df['attendance'] * df['assignments_completed']) / 100

# Select exactly the 9 features the backend expects
features = [
    'attendance', 'internal_marks', 'unit_test_marks', 
    'assignments_completed', 'study_hours_weekly', 'previous_cgpa',
    'momentum', 'effort_score', 'engagement_index'
]

X = df[features]
y = df['is_at_risk']

print("🚀 Training 9-Feature XGBoost Model...")
model = XGBClassifier(n_estimators=150, learning_rate=0.05, max_depth=6)
model.fit(X, y)

# Save the new brain!
joblib.dump(model, 'student_model.pkl')
print("⭐ Success! New 'student_model.pkl' saved with 9 features.")