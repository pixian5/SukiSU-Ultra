#!/usr/bin/env python3
"""Compare the UAPI contract between the builtin kernel branch and a release tag.

The two branches spell constants differently (DECLARE macro vs static const,
integer literals with/without a `u` suffix), so a raw text diff is noisy.
This normalises both forms and compares identifier -> value pairs.
"""
import os
import re
import sys


def strip_comments(s):
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    return re.sub(r'//[^\n]*', '', s)


def split_top(s):
    parts, depth, cur = [], 0, ''
    for c in s:
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
        if c == ',' and depth == 0:
            parts.append(cur.strip())
            cur = ''
        else:
            cur += c
    if cur.strip():
        parts.append(cur.strip())
    return parts


def norm(v):
    v = v.strip()
    v = re.sub(r'\b(\d+)[uU]\b', r'\1', v)
    v = re.sub(r'\s+', '', v)
    v = v.replace('U<<', '<<').replace('u<<', '<<')
    return v


def constants(path):
    s = strip_comments(open(path, 'rb').read().decode('utf-8-sig', errors='replace'))
    out = {}
    for m in re.finditer(r'DECLARE\s*\(', s):
        i, depth, j = m.end(), 1, m.end()
        while j < len(s) and depth:
            depth += (s[j] == '(') - (s[j] == ')')
            j += 1
        if depth:
            continue
        p = split_top(s[i:j-1])
        if len(p) >= 3:
            out[p[1]] = norm(p[2])
    for m in re.finditer(r'static const\s+\w+\s+(\w+)\s*=\s*([^;]+);', s):
        out[m.group(1)] = norm(m.group(2))
    for m in re.finditer(r'^#define\s+(\w+)\s+(.+)$', s, re.M):
        if m.group(1) != 'DECLARE':
            out.setdefault(m.group(1), norm(m.group(2)))
    return out


base, rel = sys.argv[1], sys.argv[2]
total_diff = 0
for name in sorted(os.listdir(rel)):
    if not name.endswith('.h'):
        continue
    a = constants(os.path.join(base, name)) if os.path.exists(os.path.join(base, name)) else {}
    b = constants(os.path.join(rel, name))
    diffs = [(k, a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
    total_diff += len(diffs)
    print('%-18s builtin=%3d release=%3d differing=%d' % (name, len(a), len(b), len(diffs)))
    for k, x, y in diffs:
        print('    %-42s builtin=%-30s release=%s' % (k, x, y))
print('TOTAL DIFFERING CONSTANTS:', total_diff)
