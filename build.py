"""
Единая точка сборки: PyInstaller → verify → ZIP.
Запуск: python build.py
"""
import subprocess
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(__file__)
SRC  = os.path.join(ROOT, "dist", "GalacticAcademy")
DST  = r"C:\Users\HP\Desktop\Общая\GalacticAcademy.zip"

def run(cmd, **kw):
    print(f"\n▶ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        print(f"⛔ Команда завершилась с кодом {r.returncode}")
        sys.exit(r.returncode)

# 1. Сборка
run([sys.executable, "-m", "PyInstaller", "galactic.spec", "--clean", "--noconfirm"],
    cwd=ROOT)

# 2. Верификация
run([sys.executable, "scripts/verify_build.py"], cwd=ROOT)

# 3. ZIP
print("\n▶ Упаковка в ZIP...")
import zipfile, pathlib, shutil

if os.path.exists(DST):
    os.remove(DST)

with zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    src = pathlib.Path(SRC)
    for f in src.rglob('*'):
        if f.is_file():
            zf.write(f, f.relative_to(src.parent))

mb = os.path.getsize(DST) / 1_048_576
print(f"\n🎉 Готово! {DST} — {mb:.1f} МБ")
