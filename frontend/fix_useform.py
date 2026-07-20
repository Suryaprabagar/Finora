import os
import glob
import re

files = glob.glob('d:/Myprojects/finance_APP/finora/frontend/src/components/features/**/*.tsx', recursive=True)

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'useForm<FormData>' in content:
        content = content.replace('useForm<FormData>', 'useForm')
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {file}")
