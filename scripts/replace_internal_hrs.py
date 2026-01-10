#!/usr/bin/env python3
from pathlib import Path

root = Path('.').resolve()
md_files = list(root.rglob('*.md'))
skip_dirs = ['node_modules', '.venv', '.venv-', 'venv']

for p in md_files:
    s = str(p)
    if any(x in s for x in skip_dirs):
        continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    lines = text.splitlines()
    out = []
    in_code = False
    changed = False
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code = not in_code
            out.append(line)
            continue
        # if line is exactly '---' and it's not the very first line, and not in code, replace with '***'
        if (stripped == '---' or stripped == '--- ') and idx != 0 and not in_code:
            out.append('***')
            changed = True
        else:
            out.append(line)
    if changed:
        p.write_text('\n'.join(out) + ('\n' if text.endswith('\n') else ''), encoding='utf-8')
        print('Replaced HRs in', p)
