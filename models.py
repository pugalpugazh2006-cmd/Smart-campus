from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

    def to_dict(self):
        return {'doc_id': self.id, 'username': self.username, 'role': self.role, 'email': self.email, 'password_hash': self.password_hash}

class FacultyProfile(db.Model):
    __tablename__ = 'faculty_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))
    bio = db.Column(db.Text)

    def to_dict(self):
        return {
            'doc_id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'department': self.department,
            'bio': self.bio
        }

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(50))
    semester = db.Column(db.Integer)
    parent_email = db.Column(db.String(100))
    parent_phone = db.Column(db.String(20))

    def to_dict(self):
        return {
            'doc_id': self.id, 'user_id': self.user_id, 'full_name': self.full_name,
            'roll_number': self.roll_number, 'department': self.department,
            'semester': self.semester, 'parent_email': self.parent_email,
            'parent_phone': self.parent_phone
        }

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    faculty_name = db.Column(db.String(100))
    verified_at = db.Column(db.String(50))
    distance_m = db.Column(db.Float)

    def to_dict(self):
        return {
            'doc_id': self.id,
            'student_id': self.student_id,
            'date': self.date,
            'status': self.status,
            'marked_by': self.marked_by,
            'faculty_name': self.faculty_name,
            'verified_at': self.verified_at,
            'distance_m': self.distance_m
        }

class Fee(db.Model):
    __tablename__ = 'fees'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    description = db.Column(db.String(255))
    due_date = db.Column(db.String(20))
    updated_at = db.Column(db.String(50))

    def to_dict(self):
        return {'doc_id': self.id, 'student_id': self.student_id, 'amount': self.amount, 'status': self.status, 'description': self.description, 'due_date': self.due_date, 'updated_at': self.updated_at}

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_dict(self):
        return {'doc_id': self.id, 'title': self.title, 'description': self.description, 'event_date': self.event_date, 'location': self.location, 'created_by': self.created_by}

class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    registration_date = db.Column(db.String(50))

    def to_dict(self):
        return {'doc_id': self.id, 'event_id': self.event_id, 'student_id': self.student_id}

class Performance(db.Model):
    __tablename__ = 'performance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    marks_obtained = db.Column(db.Integer, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    credits = db.Column(db.Integer, default=1)
    grade = db.Column(db.String(5))
    grade_point = db.Column(db.Float)

    def to_dict(self):
        return {'doc_id': self.id, 'student_id': self.student_id, 'subject': self.subject, 'marks_obtained': self.marks_obtained, 'total_marks': self.total_marks, 'credits': self.credits, 'grade': self.grade, 'grade_point': self.grade_point}

class QRSession(db.Model):
    __tablename__ = 'qr_sessions'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    secret = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.String(50))
    active = db.Column(db.Boolean, default=True)
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    current_token = db.Column(db.String(50))

    def to_dict(self):
        return {'doc_id': self.id, 'subject': self.subject, 'secret': self.secret, 'created_by': self.created_by, 'created_at': self.created_at, 'active': self.active, 'latitude': self.latitude, 'longitude': self.longitude, 'current_token': self.current_token}

class Transport(db.Model):
    __tablename__ = 'transport'
    id = db.Column(db.Integer, primary_key=True)
    bus_no = db.Column(db.String(20), nullable=False)
    driver = db.Column(db.String(50))
    contact = db.Column(db.String(20))
    route = db.Column(db.String(200))
    timing = db.Column(db.String(50))

    def to_dict(self):
        return {'doc_id': self.id, 'bus_no': self.bus_no, 'driver': self.driver, 'contact': self.contact, 'route': self.route, 'timing': self.timing}

class StudentTransport(db.Model):
    __tablename__ = 'student_transport'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    transport_id = db.Column(db.Integer, db.ForeignKey('transport.id'), nullable=False)
    assigned_at = db.Column(db.String(50))

    def to_dict(self):
        return {'doc_id': self.id, 'student_id': self.student_id, 'transport_id': self.transport_id, 'assigned_at': self.assigned_at}

class Library(db.Model):
    __tablename__ = 'library'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    isbn = db.Column(db.String(50))
    category = db.Column(db.String(50))
    copies = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {'doc_id': self.id, 'title': self.title, 'author': self.author, 'isbn': self.isbn, 'category': self.category, 'copies': self.copies}

class LibraryRecord(db.Model):
    __tablename__ = 'library_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('library.id'), nullable=False)
    borrow_date = db.Column(db.String(50))
    return_date = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Borrowed')

    def to_dict(self):
        return {'doc_id': self.id, 'student_id': self.student_id, 'book_id': self.book_id, 'borrow_date': self.borrow_date, 'return_date': self.return_date, 'status': self.status}

class Syllabus(db.Model):
    __tablename__ = 'syllabus'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50))
    subject = db.Column(db.String(100))
    link = db.Column(db.String(200))
    added_by = db.Column(db.String(100))
    date = db.Column(db.String(50))

    def to_dict(self):
        return {'doc_id': self.id, 'title': self.title, 'type': self.type, 'subject': self.subject, 'link': self.link, 'added_by': self.added_by, 'date': self.date}

class AdminProfile(db.Model):
    __tablename__ = 'admin_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100))

    def to_dict(self):
        return {'doc_id': self.id, 'user_id': self.user_id, 'full_name': self.full_name, 'title': self.title}
