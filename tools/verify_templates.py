#!/usr/bin/env python3
import ast
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
py_files = list(root.rglob('*.py'))
referenced = set()

def extract_from_call(node):
    # collect string literals in args for calls to render/render_to_string/TemplateResponse
    names = []
    # func name
    func = node.func
    func_name = ''
    if isinstance(func, ast.Attribute):
        func_name = func.attr
    elif isinstance(func, ast.Name):
        func_name = func.id
    # interested in render, render_to_string, TemplateResponse
    if func_name in ('render', 'render_to_string', 'TemplateResponse'):
        # first string arg or keyword 'template_name'
        for idx, arg in enumerate(node.args):
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.endswith('.html'):
                referenced.add(arg.value)
                names.append(arg.value)
                break
        for kw in node.keywords:
            if kw.arg == 'template_name' and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                referenced.add(kw.value.value)
                names.append(kw.value.value)
    return names

# also capture assignments of template_name = '...'
for p in py_files:
    try:
        src = p.read_text(encoding='utf-8')
        tree = ast.parse(src)
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            try:
                extract_from_call(node)
            except Exception:
                pass
        # attribute assignment like template_name = 'accounts/profile.html'
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'template_name':
                    val = node.value
                    if isinstance(val, ast.Constant) and isinstance(val.value, str) and val.value.endswith('.html'):
                        referenced.add(val.value)
        # also class-based view attribute
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name) and t.id == 'template_name':
                            v = stmt.value
                            if isinstance(v, ast.Constant) and isinstance(v.value, str) and v.value.endswith('.html'):
                                referenced.add(v.value)

templates_dir = root / 'templates'
# gather actual templates under any 'templates/' directory in the repo
actual = set()
for t in root.rglob('templates'):
    if t.is_dir():
        for html in t.rglob('*.html'):
            # store relative path from this templates/ dir
            rel = str(html).split(str(t) + os.sep, 1)[1].replace('\\', '/')
            actual.add(rel)

# now compute missing references
missing = sorted([r for r in referenced if r not in actual])

print('Found {} referenced templates in Python code.'.format(len(referenced)))
print('Found {} actual templates under templates/'.format(len(actual)))
print('\nMissing templates (referenced but not present):\n')
for m in missing:
    print(' -', m)

# Also find templates that exist but are not referenced (possible orphans)
unreferenced = sorted([a for a in actual if a not in referenced])
print('\nTemplates present but not referenced by views (may be used elsewhere): {}\n'.format(len(unreferenced)))
# print a short sample
for a in unreferenced[:40]:
    print(' *', a)

# Exit code non-zero if missing templates found
if missing:
    exit(2)
else:
    exit(0)
