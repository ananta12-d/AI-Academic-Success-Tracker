import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# 1. Load the dataset
print("Loading data...")
df = pd.read_csv('student_data.csv')

# 2. Prepare the data (Separate Features and Target)
# We drop 'student_name' and 'roll_no' because ML models need numbers, not text, 
# and these don't affect academic performance anyway.
X = df[['attendance', 'internal_marks', 'unit_test_marks']] 
y = df['is_at_risk'] # This is what we want to predict

# 3. Split the data into Training (80%) and Testing (20%) sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Initialize and Train the Model
print("Training the Random Forest model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Make predictions on the test set
y_pred = model.predict(X_test)

# 6. Evaluate the accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"\n✅ Model Accuracy: {accuracy * 100:.2f}%\n")
print("📊 Classification Report:")
print(classification_report(y_test, y_pred, target_names=["Not at Risk", "At Risk"]))

# --- PREDICTION INTERFACE ---
print("\n--- Test the Prediction Interface ---")
# Let's test a hypothetical student: 65% attendance, 12 internal marks, 20 unit test marks
new_student = pd.DataFrame([[65, 12, 20]], columns=['attendance', 'internal_marks', 'unit_test_marks'])
prediction = model.predict(new_student)

if prediction[0] == 1:
    print("⚠️ ALERT: This student is projected to be AT RISK. Early intervention recommended.")
else:
    print("✅ This student is on track. No immediate intervention needed.")