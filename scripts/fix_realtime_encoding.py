# -*- coding: utf-8 -*-
import re

# 读取文件
with open('front_end/realtime/static/js/realtime.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换乱码字符
content = content.replace('// ? 发送结束信号', '// ✅ 发送结束信号')
content = content.replace("'? 评估报告已生成'", "'✅ 评估报告已生成'")
content = content.replace("'? 评估报告生成失败:", "'❌ 评估报告生成失败:'")

# 写回文件
with open('front_end/realtime/static/js/realtime.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('修复完成')
