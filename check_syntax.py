import py_compile
import os
import sys

errors = []
skip_dirs = {'build', 'dist', '.git', '__pycache__', 'venv'}

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(str(e))

if errors:
    print("Syntax errors found:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("All Python files passed syntax check.")
