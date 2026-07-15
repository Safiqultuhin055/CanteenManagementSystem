"""Pre-deploy drift check — catch "works on my machine" bugs before a build.

Runs on the DEVELOPER's machine (where every import already resolves), so it
finds drift that a clean Docker build would only hit at runtime:

  1. Undeclared pip dependency — a top-level import whose distribution is NOT
     listed in requirements.txt. The author has it installed from some other
     project; a clean image does not → crash.
  2. Missing import entirely — imported but not installed anywhere.
  3. Engine-specific raw SQL in Python (T-SQL only): warned, not failed
     (this project targets SQL Server, but flag it so it's a conscious choice).

Exit code: 1 if any hard error (categories 1–2), else 0. Run before building:
    python deploy/docker/preflight.py

Note: schema-patch registration drift is handled structurally — apply_schema_patches
auto-discovers database/NN_*.sql (NN >= 23), so a new patch never needs manual wiring.
"""
import ast
import os
import re
import sys
from importlib import metadata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local top-level packages (this repo's own apps) — never third-party.
LOCAL_ROOTS = {
    'canteen_system', 'core', 'users', 'employee', 'inventory', 'balance',
    'pos', 'kitchen', 'distribution', 'reports', 'manage', 'deploy',
}

SKIP_DIRS = {'venv', '.venv', '__pycache__', '.git', 'migrations', 'node_modules'}

# Engine-specific SQL tokens (T-SQL). Portability warning only.
TSQL_TOKENS = re.compile(
    r'\b(SYSDATETIME|GETDATE|CAST\s*\([^)]*AS\s+DATE|CONVERT\s*\(|DATEPART|ISNULL|NEWID)\b'
    r'|\bTOP\s+\d+\b',
    re.IGNORECASE,
)


def _norm(name):
    """PEP 503 normalize a distribution / requirement name."""
    return re.sub(r'[-_.]+', '-', name).lower()


def _project_py_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith('.py'):
                yield os.path.join(base, f)


def _top_level_imports(path):
    try:
        tree = ast.parse(open(path, encoding='utf-8').read(), filename=path)
    except (SyntaxError, UnicodeDecodeError):
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:  # skip relative imports
                names.add(node.module.split('.')[0])
    return names


def _declared_dists():
    req = os.path.join(ROOT, 'requirements.txt')
    declared = set()
    for line in open(req, encoding='utf-8'):
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        m = re.match(r'^([A-Za-z0-9._-]+)', line)
        if m:
            declared.add(_norm(m.group(1)))
    return declared


def main():
    stdlib = getattr(sys, 'stdlib_module_names', set())
    declared = _declared_dists()
    # import name -> [distribution names], for installed packages.
    imp_to_dist = metadata.packages_distributions()

    imports = set()
    tsql_hits = []
    for path in _project_py_files():
        imports |= _top_level_imports(path)
        rel = os.path.relpath(path, ROOT)
        if os.path.basename(path) == 'preflight.py':
            continue  # don't match our own T-SQL token pattern
        # scan raw SQL only in .py that talk to a cursor
        src = open(path, encoding='utf-8', errors='ignore').read()
        if 'cursor' in src or '.execute(' in src:
            for m in TSQL_TOKENS.finditer(src):
                line = src[:m.start()].count('\n') + 1
                tsql_hits.append(f'{rel}:{line}: {m.group(0).strip()}')

    undeclared, missing = [], []
    for name in sorted(imports):
        if name in stdlib or name in LOCAL_ROOTS or name.startswith('_'):
            continue
        dists = imp_to_dist.get(name)
        if not dists:
            missing.append(name)
            continue
        if not any(_norm(d) in declared for d in dists):
            undeclared.append(f'{name} (dist: {", ".join(dists)})')

    print('=== preflight: dependency + portability drift ===')
    ok = True
    if missing:
        ok = False
        print('\n[ERROR] imported but NOT installed (add to requirements.txt):')
        for n in missing:
            print(f'  - {n}')
    if undeclared:
        ok = False
        print('\n[ERROR] imported + installed locally but MISSING from requirements.txt:')
        for n in undeclared:
            print(f'  - {n}')
    if tsql_hits:
        print(f'\n[WARN] {len(tsql_hits)} engine-specific (T-SQL) token(s) in Python — '
              'fine for SQL Server, review if the DB engine ever changes:')
        for h in tsql_hits[:40]:
            print(f'  - {h}')

    if ok:
        print('\nOK — every third-party import is declared in requirements.txt.')
        return 0
    print('\nFAILED — fix the errors above before building the image.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
