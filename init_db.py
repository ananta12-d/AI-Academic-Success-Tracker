import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash

def setup_database():
    # 1. Connect to SQLite (This automatically creates 'app.db' if it doesn't exist)
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # 2. Create the Users table (For Admin and Student logins)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # 3. Create the Semester History table 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS semester_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            semester INTEGER NOT NULL,
            attendance REAL,
            internal_marks REAL,
            unit_test_marks REAL,
            assignments_completed INTEGER,
            study_hours_weekly REAL,
            cgpa REAL,
            FOREIGN KEY (roll_no) REFERENCES users (roll_no)
        )
    ''')

    # 4. Clear existing data so we don't get duplicates if you run this twice
    cursor.execute('DELETE FROM semester_history')
    cursor.execute('DELETE FROM users')

    # 5. Create the Master Admin Account
    admin_password = generate_password_hash("admin123") # Change this later!
    cursor.execute('INSERT INTO users (roll_no, password_hash, role) VALUES (?, ?, ?)', 
                   ("ADMIN", admin_password, "admin"))

    # 6. Read the CSV and generate Student Accounts
    print("Reading student_data.csv...")
    df = pd.read_csv('student_data.csv')
    
    import random # Make sure this is imported at the top of init_db.py

    for index, row in df.iterrows():
        roll_no = row['roll_no']
        default_pw = generate_password_hash(f"pass{roll_no}")
        
        cursor.execute('INSERT INTO users (roll_no, password_hash, role) VALUES (?, ?, ?)', 
                       (roll_no, default_pw, "student"))
        
        # --- GENERATE FAKE HISTORY FOR SEM 1 & 2 ---
        base_cgpa = row['previous_cgpa']
        base_att = row['attendance']
        
        for sem in [1, 2]:
            # Slightly alter past marks to create a "trend"
            past_cgpa = max(5.0, min(10.0, base_cgpa + random.uniform(-1.5, 1.5)))
            past_att = max(40, min(100, base_att + random.randint(-15, 15)))
            
            cursor.execute('''
                INSERT INTO semester_history 
                (roll_no, semester, attendance, cgpa)
                VALUES (?, ?, ?, ?)
            ''', (roll_no, sem, past_att, past_cgpa))

        # --- INSERT CURRENT DATA AS SEMESTER 3 ---
        cursor.execute('''
            INSERT INTO semester_history 
            (roll_no, semester, attendance, internal_marks, unit_test_marks, assignments_completed, study_hours_weekly, cgpa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            roll_no, 3, row['attendance'], row['internal_marks'], row['unit_test_marks'], 
            row['assignments_completed'], row['study_hours_weekly'], row['previous_cgpa']
        ))

    # Save and close
    conn.commit()
    conn.close()
    print(f"✅ Database 'app.db' created successfully with 1 Admin and {len(df)} Students!")

if __name__ == '__main__':
    setup_database()