#!/usr/bin/env python3
from pathlib import Path

root = Path('.').resolve()
md_files = list(root.rglob('*.md'))
for p in md_files:
    try:
        text = p.read_text(encoding='utf-8')
    except Exception:
        continue
    lines = text.splitlines()
    changed = False
    new_lines = []
    for line in lines:
        if line.strip() == '````markdown' or line.strip() == '````':
            changed = True
            continue
        new_lines.append(line)
    if changed:
        p.write_text('\n'.join(new_lines) + ('\n' if text.endswith('\n') else ''), encoding='utf-8')
        print(f'Fixed: {p}')
