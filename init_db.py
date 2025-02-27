from app import app, db  # Import Flask app and db instance

def init_db():
    with app.app_context():  # Ensure app context is active
        db.create_all()
        print("Database initialized!")

if __name__ == "__main__":
    init_db()
