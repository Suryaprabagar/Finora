from app.core.security import verify_password
try:
    print(verify_password('password', 'invalidhash'))
except Exception as e:
    import traceback
    traceback.print_exc()
