import os

models_dir = r"d:\Myprojects\finance_APP\finora\backend\app\models"

for filename in os.listdir(models_dir):
    if not filename.endswith(".py") or filename == "__init__.py":
        continue
    
    filepath = os.path.join(models_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace imports
    new_content = content.replace(
        "from sqlalchemy.dialects.postgresql import UUID",
        "from sqlalchemy import Uuid"
    )
    # Replace UUID(as_uuid=True) with Uuid(as_uuid=True) or Uuid
    new_content = new_content.replace(
        "UUID(as_uuid=True)",
        "Uuid"
    )
    new_content = new_content.replace(
        "UUID",
        "Uuid"
    )
    
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {filename}")
