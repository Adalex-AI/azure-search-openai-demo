#!/usr/bin/env python3
from pathlib import Path
import re

targets = []
# If targets is empty, we will scan the whole repo

root = Path('.').resolve()

def ensure_blank_lines(lines):
    out = []
    i = 0
    n = len(lines)
    # Detect frontmatter range if valid
    frontmatter_end = -1
    if n > 0 and lines[0].strip() == '---':
        for j in range(1, min(n, 20)):
            if lines[j].strip() == '---':
                frontmatter_end = j
                break
    
    while i < n:
        line = lines[i]
        stripped = line.strip()
        # remove trailing spaces
        line = line.rstrip()
        
        # Preserve frontmatter exactly
        if i <= frontmatter_end:
             out.append(line)
             i += 1
             continue

        # Replace internal HR '---' with '***' to avoid confusion, 
        # unless it looks like a table row or something else.
        # But only if it is EXACTLY '---'.
        if stripped == '---':
             line = '***'
             stripped = '***'

        # headings: ensure blank line before
        if re.match(r'#{1,6} ', stripped):
            if out and out[-1].strip() != '':
                out.append('')
            out.append(line)
            # ensure blank line after heading if next line exists and not blank
            if i+1 < n and lines[i+1].strip() != '':
                out.append('')
            i += 1
            continue
        # fenced code block: ensure blank lines around and add bash language if missing
        if stripped.startswith('```'):
            # ensure blank line before
            if out and out[-1].strip() != '':
                out.append('')
            fence = stripped
            if fence == '```':
                fence = '```bash'
            out.append(fence)
            i += 1
            # copy until closing fence
            while i < n:
                l = lines[i].rstrip()
                out.append(l)
                if l.strip().startswith('```'):
                    break
                i += 1
            # ensure blank line after
            if i+1 < n and lines[i+1].strip() != '':
                out.append('')
            i += 1
            continue
        # lists: ensure blank line before list start
        if re.match(r'^[\-\*\+]\s+\S', stripped) or re.match(r'^\d+\.\s+\S', stripped):
            if out and out[-1].strip() != '':
                out.append('')
            out.append(line)
            # copy remaining list items
            i += 1
            while i < n and (re.match(r'^[\-\*\+]\s+\S', lines[i].strip()) or re.match(r'^\d+\.\s+\S', lines[i].strip()) or lines[i].strip()==''):
                out.append(lines[i].rstrip())
                i += 1
            # ensure blank line after list
            if i < n and lines[i].strip() != '':
                out.append('')
            continue

        # bare URL line -> convert to markdown link with hostname text
        if re.match(r'^https?://\S+$', stripped):
            url = stripped
            host = re.sub(r'^https?://', '', url).split('/')[0]
            out.append(f'[{host}]({url})')
            i += 1
            continue

        out.append(line)
        i += 1
    # remove duplicate consecutive blank lines (max one)
    final = []
    prev_blank = False
    for l in out:
        if l.strip() == '':
            if prev_blank:
                continue
            prev_blank = True
            final.append('')
        else:
            prev_blank = False
            final.append(l)
    return final


if not targets:
    # Scan all .md files
    for p in root.rglob('*.md'):
        s = str(p)
        if 'node_modules' in s or '/.venv' in s or '/.venv-' in s or '/venv' in s:
            continue
        try:
            text = p.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Skipping {p}: {e}")
            continue
            
        lines = text.splitlines()
        new_lines = ensure_blank_lines(lines)
        if not new_lines: # Safety check
            continue
            
        new_text = '\n'.join(new_lines) + ('\n' if text.endswith('\n') else '')
        if new_text != text:
             try:
                p.write_text(new_text, encoding='utf-8')
                print('Fixed:', p)
             except Exception as e:
                print(f"Failed to write {p}: {e}")
else:
    for t in targets:
        p = root / t
        if not p.exists():
            print('Missing:', t)
            continue
        text = p.read_text(encoding='utf-8')
        lines = text.splitlines()
        new_lines = ensure_blank_lines(lines)
        new_text = '\n'.join(new_lines) + ('\n' if text.endswith('\n') else '')
        if new_text != text:
            p.write_text(new_text, encoding='utf-8')
            print('Fixed:', t)
        else:
            print('OK:', t)
