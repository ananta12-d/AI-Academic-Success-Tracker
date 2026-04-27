import pandas as pd
import random
from faker import Faker

fake = Faker('en_IN')

# Authentic Odia Name Pools
odia_first_names = ['Aarav', 'Bikash', 'Chinmay', 'Debashis', 'Elina', 'Gayatree', 'Jyoti', 'Kiran', 'Manas', 'Nibedita', 'Pradeep', 'Priyanka', 'Rakesh', 'Satyajit', 'Smita', 'Soumya', 'Subhasis', 'Tapaswini']
odia_last_names = ['Das', 'Mishra', 'Mohanty', 'Panda', 'Patra', 'Rout', 'Sahoo', 'Samal', 'Tripathy', 'Behera', 'Nayak', 'Pradhan', 'Barik']

def generate_student_data(students_per_course=100):
    data = []
    courses = ['BCA', 'BSC', 'BBA'] # Simplified BSC-CS to BSC for cleaner roll numbers
    enrollment_year = "23"
    prefix = "03"
    
    for course in courses:
        for i in range(1, students_per_course + 1):
            # 50% chance of an Odia-specific name, 50% general Indian name
            if random.random() > 0.5:
                name = f"{random.choice(odia_first_names)} {random.choice(odia_last_names)}"
            else:
                name = fake.name()
                
            # Roll No Format: 03 BCA 23 001
            roll_no = f"{prefix}{course}{enrollment_year}{i:03d}" 
            
            attendance = random.randint(45, 100)
            internal_marks = random.randint(5, 30)
            unit_test_marks = random.randint(10, 50)
            assignments_completed = random.randint(0, 10)
            study_hours_weekly = random.randint(2, 20)
            previous_cgpa = round(random.uniform(5.0, 10.0), 2)
            
            at_risk = 0
            score_total = internal_marks + unit_test_marks
            
            if attendance < 60 or score_total < 35 or previous_cgpa < 6.0:
                at_risk = 1
            elif attendance < 75 and assignments_completed < 5:
                at_risk = 1
            elif 75 <= attendance <= 85 and score_total < 45:
                at_risk = random.choice([0, 1])
                
            data.append([name, roll_no, course, attendance, internal_marks, unit_test_marks, 
                         assignments_completed, study_hours_weekly, previous_cgpa, at_risk])
            
    columns = ['student_name', 'roll_no', 'course', 'attendance', 'internal_marks', 'unit_test_marks', 
               'assignments_completed', 'study_hours_weekly', 'previous_cgpa', 'is_at_risk']
    
    df = pd.DataFrame(data, columns=columns)
    return df

dataset = generate_student_data(100) # Creates 300 total students
dataset.to_csv('student_data.csv', index=False)
print("✅ Odia/Indian dataset with custom Roll Numbers generated!")