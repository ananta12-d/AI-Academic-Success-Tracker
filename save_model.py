import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier

# 1. Load the new, expanded dataset
df = pd.read_csv('student_data.csv')

# 2. Select ALL 6 features for the 'X' inputs
X = df[['attendance', 'internal_marks', 'unit_test_marks', 
        'assignments_completed', 'study_hours_weekly', 'previous_cgpa']]
y = df['is_at_risk']

# 3. Train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# 4. Save the new model to overwrite the old one
joblib.dump(model, 'student_model.pkl')
print("✅ Model successfully trained on all 6 features and saved as 'student_model.pkl'")