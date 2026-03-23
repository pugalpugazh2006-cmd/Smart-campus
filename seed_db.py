from werkzeug.security import generate_password_hash
from app import app
from mock_db import MockDB
from models import db as sql_db
import datetime
import os

db = MockDB()

def seed_database():
    with app.app_context():
        print("Seeding PostgreSQL/SQLite database...")
        sql_db.drop_all()
        sql_db.create_all()

        # 1. Create Users
        admin_id = db.table('users').insert({
            'username': 'admin',
            'password_hash': generate_password_hash('admin123'),
            'role': 'admin',
            'email': 'admin@smartcampus.com'
        })

        faculty_id = db.table('users').insert({
            'username': 'faculty1',
            'password_hash': generate_password_hash('faculty123'),
            'role': 'faculty',
            'email': 'faculty@smartcampus.com'
        })

        # Student 1 (Normal)
        student_id = db.table('users').insert({
            'username': 'student1',
            'password_hash': generate_password_hash('student123'),
            'role': 'student',
            'email': 'student@smartcampus.com'
        })

        # Student 2 (Risk: Low Attendance)
        student2_id = db.table('users').insert({
            'username': 'student2',
            'password_hash': generate_password_hash('student123'),
            'role': 'student',
            'email': 'student2@smartcampus.com'
        })

        # Student 3 (Risk: Low Marks)
        student3_id = db.table('users').insert({
            'username': 'student3',
            'password_hash': generate_password_hash('student123'),
            'role': 'student',
            'email': 'student3@smartcampus.com'
        })

        # 2. Profiles
        db.table('faculty_profiles').insert({
            'user_id': faculty_id,
            'full_name': 'Dr. Robert Smith',
            'department': 'Computer Science'
        })

        db.table('student_profiles').insert({
            'user_id': student_id,
            'full_name': 'John Doe',
            'roll_number': 'CS2024001',
            'department': 'Computer Science',
            'semester': 4,
            'parent_email': 'parent.doe@example.com',
            'parent_phone': '+919876543210'
        })

        db.table('student_profiles').insert({
            'user_id': student2_id,
            'full_name': 'Jane Smith',
            'roll_number': 'CS2024002',
            'department': 'Computer Science',
            'semester': 4,
            'parent_email': 'parent.smith@example.com',
            'parent_phone': '+919876543211'
        })

        db.table('student_profiles').insert({
            'user_id': student3_id,
            'full_name': 'Mike Ross',
            'roll_number': 'CS2024003',
            'department': 'Computer Science',
            'semester': 4,
            'parent_email': 'parent.ross@example.com',
            'parent_phone': '+919876543212'
        })

        # 3. Attendance (Generating history for risk analysis)
        today = datetime.datetime.now()
        for i in range(10):
            date_str = (today - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            # Student 1: 100% attendance
            db.table('attendance').insert({'student_id': student_id, 'date': date_str, 'status': 'Present', 'marked_by': faculty_id})
            
            # Student 2: 20% attendance (Present only on the last 2 days)
            status2 = 'Present' if i < 2 else 'Absent'
            db.table('attendance').insert({'student_id': student2_id, 'date': date_str, 'status': status2, 'marked_by': faculty_id})
            
            # Student 3: 80% attendance
            status3 = 'Present' if i < 8 else 'Absent'
            db.table('attendance').insert({'student_id': student3_id, 'date': date_str, 'status': status3, 'marked_by': faculty_id})

        # 4. Fees
        db.table('fees').insert({
            'student_id': student_id,
            'amount': 5000.00,
            'status': 'Pending',
            'description': 'Semester 4 Tuition Fee',
            'due_date': (datetime.datetime.now() + datetime.timedelta(days=15)).strftime('%Y-%m-%d'),
            'updated_at': datetime.datetime.now().isoformat()
        })
        db.table('fees').insert({
            'student_id': student_id,
            'amount': 1500.00,
            'status': 'Overdue',
            'description': 'Hostel Maintenance Fee',
            'due_date': (datetime.datetime.now() - datetime.timedelta(days=5)).strftime('%Y-%m-%d'),
            'updated_at': datetime.datetime.now().isoformat()
        })

        # 5. Events
        event_id = db.table('events').insert({
            'title': 'Tech Symposium 2026',
            'description': 'Annual technical festival',
            'event_date': (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat(),
            'location': 'Main Auditorium',
            'created_by': admin_id
        })

        # 6. Performance
        # Student 1: Good
        db.table('performance').insert({
            'student_id': student_id, 'subject': 'Data Structures', 'marks_obtained': 85, 'total_marks': 100, 'credits': 4, 'grade': 'A', 'grade_point': 9.0
        })
        
        # Student 2: Good Academics, but poor attendance
        db.table('performance').insert({
            'student_id': student2_id, 'subject': 'Data Structures', 'marks_obtained': 82, 'total_marks': 100, 'credits': 4, 'grade': 'A', 'grade_point': 9.0
        })

        # Student 3: Poor Academics
        db.table('performance').insert({
            'student_id': student3_id, 'subject': 'Data Structures', 'marks_obtained': 35, 'total_marks': 100, 'credits': 4, 'grade': 'F', 'grade_point': 0.0
        })

        db.table('performance').insert({
            'student_id': student_id,
            'subject': 'Mathematics',
            'marks_obtained': 78,
            'total_marks': 100,
            'credits': 4,
            'grade': 'B+',
            'grade_point': 8.0
        })

        # 7. Library
        book1_id = db.table('library').insert({
            'title': 'The Clean Coder',
            'author': 'Robert C. Martin',
            'isbn': '978-0137081073',
            'category': 'Computer Science',
            'copies': 5
        })
        book2_id = db.table('library').insert({
            'title': 'Introduction to Algorithms',
            'author': 'Cormen, Leiserson, Rivest, Stein',
            'isbn': '978-0262033848',
            'category': 'Computer Science',
            'copies': 2
        })
        db.table('library').insert({
            'title': 'A Brief History of Time',
            'author': 'Stephen Hawking',
            'isbn': '978-0553109531',
            'category': 'Physics',
            'copies': 3
        })

        # 8. Borrow Record
        db.table('library_records').insert({
            'student_id': student_id,
            'book_id': book1_id,
            'borrow_date': datetime.datetime.now().isoformat(),
            'status': 'Borrowed'
        })

        # 9. Transport
        bus1_id = db.table('transport').insert({
            'bus_no': 'B-01',
            'driver': 'Rahul Sharma',
            'contact': '+919988776655',
            'route': 'Main Square - City Center - East Campus',
            'timing': '08:00 AM'
        })
        bus2_id = db.table('transport').insert({
            'bus_no': 'B-02',
            'driver': 'Amit Kumar',
            'contact': '+919988776644',
            'route': 'North Blocks - Metro Station - Main Gate',
            'timing': '08:15 AM'
        })

        # 10. Student Transport Assignment
        db.table('student_transport').insert({
            'student_id': student_id,
            'transport_id': bus1_id,
            'assigned_at': datetime.datetime.now().isoformat()
        })

        print("Database seeded successfully!")
        print("\nLogin credentials:")
        print("Admin: admin / admin123")
        print("Faculty: faculty1 / faculty123")
        print("Student: student1 / student123")

if __name__ == "__main__":
    seed_database()
