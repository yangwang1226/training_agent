# -*- coding: utf-8 -*-

with open('front_end/realtime/static/js/realtime.js', 'r', encoding='utf-8') as f:
    content = f.read()

check_items = [
    ('Check mark (U+2705)', '✅' in content),
    ('Cross mark (U+274C)', '❌' in content),
    ('Save message', '正在保存对话记录和生成评估报告' in content),
    ('Success message', '评估报告已生成' in content),
    ('Error message', '评估报告生成失败' in content),
]

print('=== File Encoding Verification ===')
all_passed = True
for name, result in check_items:
    status = '[OK]' if result else '[FAIL]'
    print(f'{status} {name}')
    if not result:
        all_passed = False

if all_passed:
    print('\n[SUCCESS] All Chinese characters and emoji are correctly encoded!')
    print('The file is ready for testing.')
else:
    print('\n[WARNING] Some content not found')
