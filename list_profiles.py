from tinydb import TinyDB, Query
from config import Config

def list_student_profiles():
    db = TinyDB(Config.DB_FILE)
    profiles = db.table('student_profiles').all()
    print(f"{'User ID':<8} | {'Full Name':<20} | {'Roll Number':<15}")
    print("-" * 50)
    for p in profiles:
        print(f"{p.get('user_id', 'N/A'):<8} | {p.get('full_name', 'N/A'):<20} | {p.get('roll_number', 'N/A'):<15}")

if __name__ == "__main__":
    list_student_profiles()
