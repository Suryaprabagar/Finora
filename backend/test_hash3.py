from app.core.security import get_password_hash
try:
    print("Hashing:", get_password_hash("password123"))
except Exception as e:
    import traceback
    traceback.print_exc()
