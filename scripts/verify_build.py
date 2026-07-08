"""
Post-build верификатор: запускай после PyInstaller.
Проверяет структуру дистрибутива до упаковки в ZIP.
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

ROOT   = os.path.dirname(os.path.dirname(__file__))
DIST   = os.path.join(ROOT, "dist", "GalacticAcademy")
INTERN = os.path.join(DIST, "_internal")

CHECKS = []
ERRORS = []

def ok(msg):   CHECKS.append(f"  ✅ {msg}")
def fail(msg): ERRORS.append(f"  ❌ {msg}")

# 1. EXE существует и не маленький
exe = os.path.join(DIST, "GalacticAcademy.exe")
if os.path.exists(exe):
    mb = os.path.getsize(exe) / 1_048_576
    ok(f"EXE существует — {mb:.1f} МБ")
    if mb < 5:
        fail(f"EXE слишком маленький ({mb:.1f} МБ) — сборка неполная")
else:
    fail("GalacticAcademy.exe не найден")

# 2. .env внутри _internal
env_path = os.path.join(INTERN, ".env")
if os.path.exists(env_path):
    content = open(env_path).read()
    if "OPENROUTER_API_KEY" in content and len(content.strip()) > 20:
        ok(".env присутствует и содержит OPENROUTER_API_KEY")
    else:
        fail(".env есть, но OPENROUTER_API_KEY пустой или отсутствует")
else:
    fail(f".env не найден в {env_path}")

# 3. customtkinter data
ctk_dir = os.path.join(INTERN, "customtkinter")
if os.path.isdir(ctk_dir):
    ok("customtkinter data присутствует")
else:
    fail("customtkinter data отсутствует — тема не загрузится")

# 4. Критичные Python-модули в архиве
pylib = os.path.join(INTERN, "base_library.zip")
if os.path.exists(pylib):
    ok("base_library.zip присутствует")
else:
    fail("base_library.zip отсутствует")

# 5. Общий размер дистрибутива
total = sum(
    os.path.getsize(os.path.join(dp, f))
    for dp, _, files in os.walk(DIST)
    for f in files
)
total_mb = total / 1_048_576
if total_mb > 50:
    ok(f"Общий размер дистрибутива: {total_mb:.0f} МБ")
else:
    fail(f"Дистрибутив слишком мал: {total_mb:.0f} МБ")

# --- Отчёт ---
print("\n📦 Верификация сборки GalacticAcademy")
print("=" * 45)
for c in CHECKS:
    print(c)
for e in ERRORS:
    print(e)

if ERRORS:
    print(f"\n⛔ {len(ERRORS)} ошибок — не упаковывай в ZIP до исправления!")
    sys.exit(1)
else:
    print(f"\n✅ Все {len(CHECKS)} проверок прошли — можно паковать ZIP.")
    sys.exit(0)
