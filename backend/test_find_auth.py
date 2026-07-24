import os
def find_get_current_user(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if 'venv' in dirpath:
            continue
        for file in filenames:
            if file.endswith('.py'):
                try:
                    with open(os.path.join(dirpath, file), 'r', encoding='utf-8') as f:
                        if 'def get_current_user' in f.read():
                            print(f"Found in: {os.path.join(dirpath, file)}")
                except:
                    pass
find_get_current_user('d:\\Myprojects\\finance_APP\\finora\\backend\\app')
