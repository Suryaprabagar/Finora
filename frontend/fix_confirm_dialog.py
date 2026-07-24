import os
import glob
import re

files = glob.glob('d:/Myprojects/finance_APP/finora/frontend/src/app/(dashboard)/**/page.tsx', recursive=True)

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    if '<ConfirmDialog' in content:
        content = re.sub(r'isOpen=\{', r'open={', content)
        content = re.sub(r'onClose=\{', r'onCancel={', content)
        content = re.sub(r'confirmText=\{', r'confirmLabel={', content)
        content = re.sub(r'isDestructive\s', r'variant="danger"\n      ', content)
        content = re.sub(r'isDestructive\n', r'variant="danger"\n', content)
        content = re.sub(r'isDestructive\r\n', r'variant="danger"\r\n', content)
        
        # In case isDestructive is the last prop
        content = re.sub(r'isDestructive/>', r'variant="danger"\n/>', content)
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {file}")
