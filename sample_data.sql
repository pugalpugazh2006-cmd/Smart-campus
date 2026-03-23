-- Inserting Sample Data for Testing

USE smart_campus;

-- Insert Users (Passwords are 'password123' hashed)
-- password123 hashed: scrypt:32768:8:1$7e9a8f... (using dummy hash for sql, will be updated by flask if needed)
INSERT INTO users (username, password_hash, role, email) VALUES 
('admin', 'scrypt:32768:8:1$n0S8G5bX9kC2hT3p$70604b9b940e4f4e7c7e5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a', 'admin', 'admin@smartcampus.edu'),
('faculty1', 'scrypt:32768:8:1$n0S8G5bX9kC2hT3p$70604b9b940e4f4e7c7e5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a', 'faculty', 'faculty1@smartcampus.edu'),
('student1', 'scrypt:32768:8:1$n0S8G5bX9kC2hT3p$70604b9b940e4f4e7c7e5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a', 'student', 'student1@smartcampus.edu');

-- Insert Profiles
INSERT INTO faculty_profiles (user_id, full_name, department) VALUES 
(2, 'Dr. Smith', 'Computer Science');

INSERT INTO student_profiles (user_id, full_name, roll_number, department, semester) VALUES 
(3, 'John Doe', 'CS2023001', 'Computer Science', 6);

-- Insert Sample Attendance
INSERT INTO attendance (student_id, date, status, marked_by) VALUES 
(3, '2024-03-01', 'Present', 2),
(3, '2024-03-02', 'Present', 2),
(3, '2024-03-03', 'Absent', 2),
(3, '2024-03-04', 'Present', 2);

-- Insert Fee Record
INSERT INTO fees (student_id, amount, status, description) VALUES 
(3, 50000.00, 'Pending', 'Semester 6 Tuition Fee');

-- Insert Event
INSERT INTO events (title, description, event_date, location, created_by) VALUES 
('Tech Fest 2024', 'Annual technical symposium', '2024-04-10 10:00:00', 'Main Auditorium', 1);

-- Insert Performance (Internal Marks)
INSERT INTO performance (student_id, subject, marks_obtained, total_marks) VALUES 
(3, 'Python Programming', 85, 100),
(3, 'Database Management', 78, 100),
(3, 'Web Development', 92, 100),
(3, 'Operating Systems', 65, 100);
