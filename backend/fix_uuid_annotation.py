import os

models_dir = r"d:\Myprojects\finance_APP\finora\backend\app\models"

for filename in os.listdir(models_dir):
    if not filename.endswith(".py") or filename == "__init__.py":
        continue
    
    filepath = os.path.join(models_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Revert uuid.Uuid type annotations to uuid.UUID
    new_content = content.replace("uuid.Uuid", "uuid.UUID")
    
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed type annotation in {filename}")
