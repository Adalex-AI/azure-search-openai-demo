#!/usr/bin/env python3
from pathlib import Path

p = Path('docs/expansion/IMPLEMENTATION_SUMMARY.md')
if not p.exists():
    print('Missing', p)
    raise SystemExit(1)
text = p.read_text(encoding='utf-8')
new = text.replace('````markdown', '```markdown').replace('````', '```')
if new != text:
    p.write_text(new, encoding='utf-8')
    print('Replaced occurrences in', p)
else:
    print('No occurrences found in', p)
