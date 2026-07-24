import os
def check_imports(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if 'venv' in dirpath:
            continue
        for file in filenames:
            if file.endswith('.py'):
                try:
                    with open(os.path.join(dirpath, file), 'r', encoding='utf-8') as f:
                        if 'from app.core.security import get_current_user' in f.read():
                            print(f"Bad import in: {os.path.join(dirpath, file)}")
                except:
                    pass
check_imports('d:\\Myprojects\\finance_APP\\finora\\backend\\app')
