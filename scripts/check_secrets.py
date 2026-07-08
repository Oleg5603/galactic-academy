"""Pre-commit guard: блокирует коммит если в staged-файлах найден API-ключ."""
import subprocess
import re
import sys

FORBIDDEN = [
    (r'sk-or-v1-[a-f0-9]{40,}', "OpenRouter key"),
    (r'sk-[a-zA-Z0-9]{40,}',    "OpenAI-style key"),
    (r'OPENROUTER_API_KEY\s*=\s*["\']?sk-', "Hardcoded env key"),
    (r'ELEVENLABS_API_KEY\s*=\s*["\']?\w{20,}', "ElevenLabs key"),
]

SCAN_EXTS = {'.py', '.js', '.ts', '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini'}

def staged_files():
    r = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                       capture_output=True, text=True)
    return [f for f in r.stdout.strip().split('\n') if f]

def staged_content(path):
    r = subprocess.run(['git', 'show', f':{path}'], capture_output=True)
    return r.stdout.decode('utf-8', errors='ignore')

issues = []
for f in staged_files():
    ext = '.' + f.rsplit('.', 1)[-1] if '.' in f else ''
    if ext not in SCAN_EXTS:
        continue
    content = staged_content(f)
    for pat, label in FORBIDDEN:
        if re.search(pat, content):
            issues.append(f"  {f} → {label}")

if issues:
    print("\n🔐 СТОП — найдены секреты в коммите:")
    for i in issues:
        print(i)
    print("\nПеренеси ключи в .env и добавь .env в .gitignore\n")
    sys.exit(1)

sys.exit(0)
