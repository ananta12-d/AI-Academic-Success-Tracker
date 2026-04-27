import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from datetime import timedelta
import sqlite3
import pandas as pd
import joblib
import shap
import json
import google.generativeai as genai
from datetime import date

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'super_secret_ai_dashboard_key' 
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30) 
jwt = JWTManager(app)
# Load environment variables from .env file
load_dotenv()

# Grab the key (you mentioned you named it 'api_key' inside the .env file)
HF_TOKEN = os.getenv('api_key') 
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
# We will use Gemini 1.5 Flash - it is lightning fast and perfect for this
llm_model = genai.GenerativeModel('gemini-2.5-flash')
model = joblib.load('student_model.pkl')
explainer = shap.TreeExplainer(model)
ai_usage_tracker = {}
def get_db_connection():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row 
    return conn

# --- AUTH ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        roll_no = data.get('roll_no')
        password = data.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE roll_no = ?', (roll_no,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            # NEW: Convert the dictionary to a JSON string
            user_data = json.dumps({'roll_no': user['roll_no'], 'role': user['role']})
            access_token = create_access_token(identity=user_data)
            
            return jsonify({'token': access_token, 'role': user['role']}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    return render_template('login.html')

# --- PAGE ROUTES ---
@app.route('/')
def root():
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    return render_template('index.html')

@app.route('/student')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

# --- API ROUTES ---
@app.route('/api/my_data')
@jwt_required()
def get_my_data():
    current_user = json.loads(get_jwt_identity()) 
    if current_user['role'] != 'student':
        return jsonify({'error': 'Unauthorized'}), 401
        
    roll_no = current_user['roll_no']
    df = pd.read_csv('student_data.csv')
    student_name = df[df['roll_no'] == roll_no]['student_name'].values[0]
    
    conn = get_db_connection()
    history = conn.execute('SELECT semester, attendance, cgpa FROM semester_history WHERE roll_no = ? ORDER BY semester', (roll_no,)).fetchall()
    current = conn.execute('SELECT * FROM semester_history WHERE roll_no = ? AND semester = 3', (roll_no,)).fetchone()
    conn.close()

    sem_1_cgpa = history[0]['cgpa'] if len(history) > 0 else current['cgpa']
    momentum = current['cgpa'] - sem_1_cgpa
    effort = (current['internal_marks'] + current['unit_test_marks']) / (current['study_hours_weekly'] + 1)
    engagement = (current['attendance'] * current['assignments_completed']) / 100

    input_data = pd.DataFrame([[
        current['attendance'], current['internal_marks'], current['unit_test_marks'],
        current['assignments_completed'], current['study_hours_weekly'], current['cgpa'],
        momentum, effort, engagement
    ]], columns=['attendance', 'internal_marks', 'unit_test_marks', 'assignments_completed', 
                 'study_hours_weekly', 'previous_cgpa', 'momentum', 'effort_score', 'engagement_index'])
    
    prediction = model.predict(input_data)[0]

    return jsonify({
        'roll_no': roll_no,
        'student_name': student_name,
        'current_stats': dict(current),
        'history': [dict(h) for h in history],
        'predicted_risk': int(prediction)
    })

def clean_input(val):
    try: return float(val) if val not in [None, ''] else 0.0
    except ValueError: return 0.0

@app.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    current_user = json.loads(get_jwt_identity())
    if current_user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    attendance = clean_input(data.get('attendance'))
    internal = clean_input(data.get('internal_marks'))
    unit = clean_input(data.get('unit_test_marks'))
    assignments = clean_input(data.get('assignments_completed'))
    study_hours = clean_input(data.get('study_hours_weekly'))
    prev_cgpa = clean_input(data.get('previous_cgpa'))
    sem_1_cgpa = clean_input(data.get('cgpa_sem_1', prev_cgpa)) 
    
    momentum = prev_cgpa - sem_1_cgpa
    effort = (internal + unit) / (study_hours + 1)
    engagement = (attendance * assignments) / 100

    input_data = pd.DataFrame([[
        attendance, internal, unit, assignments, study_hours, prev_cgpa, 
        momentum, effort, engagement
    ]], columns=['attendance', 'internal_marks', 'unit_test_marks', 'assignments_completed', 
                 'study_hours_weekly', 'previous_cgpa', 'momentum', 'effort_score', 'engagement_index'])
    
    prediction = model.predict(input_data)[0]
    shap_values = explainer.shap_values(input_data)
    
    feature_impacts = []
    for feature_name, impact_score in zip(input_data.columns, shap_values[0]):
        feature_impacts.append({
            'feature': feature_name.replace('_', ' ').title(),
            'impact': float(impact_score)
        })
        
    top_drivers = sorted(feature_impacts, key=lambda x: abs(x['impact']), reverse=True)

    return jsonify({'at_risk': int(prediction), 'ai_drivers': top_drivers[:3]})

@app.route('/api/generate_action_plan', methods=['POST'])
@jwt_required()
def generate_action_plan():
    # 1. IDENTIFY THE STUDENT
    current_user = json.loads(get_jwt_identity())
    roll_no = current_user['roll_no']
    today = str(date.today())

    # 2. CHECK THE RATE LIMIT (2 uses per day)
    user_usage = ai_usage_tracker.get(roll_no, {'date': today, 'count': 0})
    
    # If it's a new day, reset their count
    if user_usage['date'] != today:
        user_usage = {'date': today, 'count': 0}
        
    if user_usage['count'] >= 2:
        # If they hit the limit, send back a colorful HTML error message
        limit_msg = """
        <div style="text-align: center; padding: 10px;">
            <h3 style="color: #ef4444; margin-bottom: 5px;">🛑 Daily Limit Reached</h3>
            <p style="opacity: 0.8;">You have used your 2 AI Action Plans for today. Focus on these goals and check back tomorrow!</p>
        </div>
        """
        return jsonify({'ai_plan': limit_msg})

    # 3. GATHER DATA
    data = request.json
    student_profile = f"""
    Attendance: {data.get('attendance')}%
    Internal Marks: {data.get('internal_marks')}/30
    Unit Test Marks: {data.get('unit_test_marks')}/50
    Assignments Completed: {data.get('assignments_completed')}/10
    Study Hours/Week: {data.get('study_hours_weekly')}
    Current Prediction: {'At Risk of Failing' if data.get('predicted_risk') == 1 else 'On Track to Pass'}
    """

    
    # 4. THE MAGIC PROMPT (Strict HTML constraints)
    prompt = f"""
    You are an upbeat, incredibly encouraging Academic Success Coach.
    Look at this student's data and write exactly 3 brief, powerful, and highly specific tips to help them improve.

    Formatting Rules:
    1. Output strictly in basic HTML format. Do NOT wrap it in ```html markdown code blocks. Just return the raw HTML.
    2. ONLY use these exact tags: <ul>, <li>, <strong>, and <span>. 
    3. ABSOLUTELY NO <div>, <p>, tables, grid, flexbox, floats, or layout-altering CSS. Keep the structure completely linear.
    4. Start each <li> with a relevant emoji.
    5. Highlight key phrases or numbers using inline CSS colors on <strong> tags (e.g., <strong style="color: #10b981;">). Use green (#10b981), blue (#3b82f6), and orange (#f59e0b).
    6. Keep each tip to a maximum of 2 short, flowing sentences. Read normally from left to right.

    Student Data:
    {student_profile}
    """

    try:
        response = llm_model.generate_content(prompt)
        
        # Clean the response in case Gemini accidentally added markdown formatting
        clean_html = response.text.replace("```html", "").replace("```", "").strip()
        
        # 5. INCREMENT THE COUNTER (Since it succeeded)
        user_usage['count'] += 1
        ai_usage_tracker[roll_no] = user_usage
        
        return jsonify({'ai_plan': clean_html})
        
    except Exception as e:
        print("Gemini API Error:", str(e))
        return jsonify({'ai_plan': "<span style='color: #ef4444;'>⚠️ The AI Advisor is resting. Please try again later.</span>"}), 200


@app.route('/api/generate_admin_report', methods=['POST'])
@jwt_required()
def generate_admin_report():
    current_user = json.loads(get_jwt_identity())
    if current_user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.json
    report_type = data.get('type') # Can be 'student' or 'class'

    try:
        if report_type == 'student':
            prompt = f"""
            You are a formal, professional Professor writing a progress report remark to a student's parents.
            Student Name: {data.get('name')}
            Attendance: {data.get('attendance')}%
            Total Marks: {data.get('marks')}/80
            Assignments: {data.get('assignments')}/10
            
            Write a single, highly professional 4-5 sentence paragraph addressing the parents. 
            Highlight their strengths, gently address any weaknesses, and suggest a path forward. 
            Do not use emojis, markdown, or bullet points. Just standard paragraph text.
            """
        else:
            prompt = f"""
            You are a Senior Academic Consultant. Analyze this data for Course {data.get('course')}:
            Pass Rate: {data.get('pass_rate')}%
            Students at Risk: {data.get('at_risk_count')} out of {data.get('total_students')}
            
            Task:
            1. Write a formal 3-sentence Executive Summary for the Dean.
            2. Provide a 'Mentor Verdict' consisting of exactly 2 short, bulleted action points for the class mentors to implement immediately.
            
            Format your response exactly like this:
            [Summary Text] ||| [Mentor Point 1] • [Mentor Point 2]
            
            Do not use markdown headers or bolding.
            """

        response = llm_model.generate_content(prompt)
        return jsonify({'report': response.text.strip()})
        
    except Exception as e:
        print("Gemini API Error:", str(e))
        return jsonify({'report': "Automated remarks are currently unavailable. Please refer to the raw metrics."}), 200
    

@app.route('/api/students/<course>')
@jwt_required()
def get_students_by_course(course):
    current_user = json.loads(get_jwt_identity())
    if current_user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    df = pd.read_csv('student_data.csv')
    if course != 'ALL': df = df[df['course'] == course]
    
    if 'cgpa_sem_1' not in df.columns: df['cgpa_sem_1'] = df['previous_cgpa']
        
    df['momentum'] = df['previous_cgpa'] - df['cgpa_sem_1']
    df['effort_score'] = (df['internal_marks'] + df['unit_test_marks']) / (df['study_hours_weekly'] + 1)
    df['engagement_index'] = (df['attendance'] * df['assignments_completed']) / 100
    
    features = df[['attendance', 'internal_marks', 'unit_test_marks', 'assignments_completed', 
                   'study_hours_weekly', 'previous_cgpa', 'momentum', 'effort_score', 'engagement_index']]
                   
    df['predicted_risk'] = model.predict(features)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/course_stats/<course>')
@jwt_required()
def get_course_stats(course):
    current_user = json.loads(get_jwt_identity())
    if current_user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    df = pd.read_csv('student_data.csv')
    if course != 'ALL': df = df[df['course'] == course]
    stats = {'avg_attendance': df['attendance'].mean(), 'avg_internal': df['internal_marks'].mean(), 'avg_unit': df['unit_test_marks'].mean()}
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)