# -*- coding: utf-8 -*-

with open('front_end/realtime/static/js/realtime.js', 'r', encoding='utf-8') as f:
    content = f.read()

check_items = [
    ('✅ 勾号', '✅' in content),
    ('❌ 叉号', '❌' in content),
    ('正在保存提示', '正在保存对话记录和生成评估报告' in content),
    ('评估报告已生成', '评估报告已生成' in content),
    ('评估报告生成失败', '评估报告生成失败' in content),
]

print('=== 文件编码修复验证 ===')
all_passed = True
for name, result in check_items:
    status = 'OK' if result else 'FAIL'
    print(f'{status}: {name}')
    if not result:
        all_passed = False

if all_passed:
    print('\n修复成功! 所有文本都已正确编码。')
else:
    print('\n警告: 部分内容未找到')
