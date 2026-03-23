from tinydb import TinyDB, Query
from werkzeug.security import check_password_hash
from config import Config

def test_login(username, password):
    db = TinyDB(Config.DB_FILE)
    User = Query()
    user = db.table('users').get(User.username == username)
    
    if not user:
        print(f"User '{username}' not found.")
        return
    
    if check_password_hash(user['password_hash'], password):
        print(f"Login successful for '{username}'!")
    else:
        print(f"Login failed for '{username}'. Incorrect password.")

if __name__ == "__main__":
    test_login('student1', 'student123')
    test_login('admin', 'admin123')
