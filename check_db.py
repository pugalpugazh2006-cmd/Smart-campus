import os
from tinydb import TinyDB
from config import Config

def check_connection():
    print("--- Smart Campus TinyDB Diagnostic ---")
    try:
        if not os.path.exists(Config.DB_FILE):
            print(f"[ERROR] Database file '{Config.DB_FILE}' not found.")
            print("Tip: Run 'python seed_db.py' to initialize the database.")
            return

        db = TinyDB(Config.DB_FILE)
        print(f"[SUCCESS] Database file '{Config.DB_FILE}' found and loaded.")
        
        # Check tables
        tables = db.tables()
        required_tables = {'users', 'faculty_profiles', 'student_profiles', 'attendance', 'fees', 'events', 'performance'}
        
        missing = [t for t in required_tables if t not in tables]
        
        if not missing:
            print("[SUCCESS] All required tables found.")
            user_count = len(db.table('users'))
            print(f"[INFO] Total users in database: {user_count}")
        else:
            print(f"[WARN] Some tables are missing: {', '.join(missing)}")
            print("Tip: Run 'python seed_db.py' to re-initialize your data.")
        
    except Exception as e:
        print(f"[ERROR] Diagnostic failed.")
        print(f"   Reason: {e}")

if __name__ == "__main__":
    check_connection()
