import os
import glob
import re

directories = [
    "app/api/v1",
    "app/modules/goals"
]

for d in directories:
    for filepath in glob.glob(os.path.join(d, "*.py")):
        with open(filepath, "r") as f:
            content = f.read()
        
        # Replace @router.METHOD("/") with @router.METHOD("")
        new_content = re.sub(r'@router\.(get|post|put|delete|patch)\("/"', r'@router.\1(""', content)
        
        if content != new_content:
            with open(filepath, "w") as f:
                f.write(new_content)
            print(f"Updated {filepath}")
