import os
import shutil
import sys

print("Looking for Chrome on GitHub Actions Windows runner...")

# GitHub Actions Windows runner has Chrome pre-installed
chrome_candidates = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

chrome_path = None
for path in chrome_candidates:
    print(f"Checking: {path}")
    if os.path.exists(path):
        chrome_path = path
        print(f"Found Chrome: {path}")
        break

if not chrome_path:
    print("Searching all drives...")
    for base in [r"C:\Program Files", r"C:\Program Files (x86)"]:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            for f in files:
                if f.lower() == "chrome.exe":
                    chrome_path = os.path.join(root, f)
                    print(f"Found: {chrome_path}")
                    break
            if chrome_path:
                break

if not chrome_path:
    print("Chrome not found, listing Program Files:")
    for base in [r"C:\Program Files", r"C:\Program Files (x86)"]:
        if os.path.exists(base):
            print(f"\n{base}:")
            for item in os.listdir(base):
                print(f"  {item}")
    sys.exit(1)

# Copy Chrome directory
chrome_dir = os.path.dirname(chrome_path)
dest = os.path.join(os.getcwd(), "browser")

if os.path.exists(dest):
    shutil.rmtree(dest)

print(f"Copying Chrome from: {chrome_dir}")
shutil.copytree(chrome_dir, dest)

total = sum(
    os.path.getsize(os.path.join(dp, f))
    for dp, dn, fn in os.walk(dest)
    for f in fn
)
print(f"Done. Size: {total/1024/1024:.1f} MB")
print(f"Chrome copied to: {dest}")
