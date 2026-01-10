#!/usr/bin/env python3
from pathlib import Path

paths = [
    Path('docs/expansion/IMPLEMENTATION_SUMMARY.md')
]

for p in paths:
    if not p.exists():
        print('Missing', p)
        continue
    text = p.read_text(encoding='utf-8')
    lines = text.splitlines()
    changed = False
    out = []
    for line in lines:
        if line.strip().startswith('````'):
            # convert any leading four backticks (with optional language) to triple
            new = line.replace('````', '```', 1)
            out.append(new)
            changed = True
        else:
            out.append(line)
    if changed:
        p.write_text('\n'.join(out) + ('\n' if text.endswith('\n') else ''), encoding='utf-8')
        print('Normalized', p)
    else:
        print('No change', p)
