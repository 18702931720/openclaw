#!/usr/bin/env python3
import html

with open('scripts/product-trending-daily.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to escape all non-ASCII characters in f-string literals.
# Strategy: for each line that contains an f-string, escape non-ASCII chars.
# An f-string line is one that starts with (or contains) f""" or f'...

import re

lines = content.split('\n')
result = []
in_fstring = False
fstring_start = None
fstring_char = None
buffer = []

for i, line in enumerate(lines):
    # Check if this line starts a multi-line f-string
    if 'f"""' in line or "f'''" in line:
        in_fstring = True
        fstring_char = '"""' if 'f"""' in line else "'''"
    elif in_fstring and ('"""' in line or "'''" in line):
        in_fstring = False
    
    if in_fstring:
        # Replace non-ASCII with HTML entities
        cleaned = ''
        for c in line:
            if ord(c) >= 128:
                cleaned += html.escape(c)
            else:
                cleaned += c
        result.append(cleaned)
    else:
        result.append(line)

with open('scripts/product-trending-daily.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(result))
print('Done')