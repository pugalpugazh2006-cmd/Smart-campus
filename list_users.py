from tinydb import TinyDB, Query
from config import Config

def list_users():
    db = TinyDB(Config.DB_FILE)
    users = db.table('users').all()
    print(f"{'Username':<20} | {'Role':<10} | {'ID':<5}")
    print("-" * 40)
    for user in users:
        print(f"{user.get('username', 'N/A'):<20} | {user.get('role', 'N/A'):<10} | {user.doc_id}")

if __name__ == "__main__":
    list_users()
