#!/usr/bin/env python3
import sys
from pathlib import Path

root = Path('.').resolve()
md_files = list(root.rglob('*.md'))
problems = []
for p in md_files:
    # Skip dependencies and virtualenvs
    s = str(p)
    if 'node_modules' in s or '/.venv' in s or '/.venv-' in s or '/venv' in s:
        continue
    try:
        text = p.read_text(encoding='utf-8')
    except Exception as e:
        problems.append((str(p), f'read_error: {e}'))
        continue
    lines = text.splitlines()
    # Count lines that are exactly '---'
    dash_lines = [i+1 for i,l in enumerate(lines) if l.strip()=='---']
    code_fences = [i+1 for i,l in enumerate(lines) if l.strip().startswith('```')]
    issues = []
    if dash_lines and len(dash_lines) % 2 == 1:
        issues.append(f"odd_---_count ({len(dash_lines)}) lines: {dash_lines[:3]}{'...' if len(dash_lines)>3 else ''}")
        # Also flag if first line is '---'
        if lines and lines[0].strip()=='---':
            issues.append('starts_with_---')
    if len(code_fences) % 2 == 1:
        issues.append(f"odd_code_fence_count ({len(code_fences)})")
    if issues:
        problems.append((str(p), ' ; '.join(issues)))

if not problems:
    print('No issues found')
    sys.exit(0)

print('Found issues in the following files:')
for p,issue in problems:
    print(p, '->', issue)

sys.exit(0)
