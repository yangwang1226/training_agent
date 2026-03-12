# -*- coding: utf-8 -*-
import sys

# 强制使用UTF-8输出
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

with open('front_end/realtime/static/js/realtime.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('Line 217:', lines[216].strip())
print('Line 328:', lines[327].strip())
print('Line 335:', lines[334].strip())

print('\nUnicode check:')
for char in lines[216]:
    if ord(char) > 127:
        print(f'  Char: {char}, Code: U+{ord(char):04X}')
