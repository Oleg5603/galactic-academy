import sys, os, traceback
sys.path.insert(0, os.path.dirname(__file__))

# Грузим .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

errors = []

# 1. Тест импортов
for mod in ["ai_analyzer", "ui.app", "ui.debate_window", "tts.voice"]:
    try:
        __import__(mod)
        print(f"OK import {mod}")
    except Exception as e:
        err = f"FAIL import {mod}: {e}"
        print(err); errors.append(err)

# 2. Тест ask_character
try:
    from ai_analyzer import ask_character
    r = ask_character("yoda", "Акупунктура — воздействие на биологически активные точки.")
    print(f"OK ask_character yoda: {len(r)} chars")
    if r.startswith("⚠️"):
        errors.append(f"API ERROR: {r}")
        print(f"API ERROR: {r}")
except Exception as e:
    err = f"FAIL ask_character: {traceback.format_exc()}"
    print(err); errors.append(err)

# 3. Тест summarize_debate
try:
    from ai_analyzer import summarize_debate
    r = summarize_debate("тест текст", {"yoda": "тезис", "vader": "вопрос"})
    print(f"OK summarize_debate: {len(r)} chars")
except Exception as e:
    err = f"FAIL summarize_debate: {traceback.format_exc()}"
    print(err); errors.append(err)

# Итог
print("\n--- ИТОГ ---")
if errors:
    for e in errors:
        print("ERROR:", e)
else:
    print("Всё OK")

with open("test_diag_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(errors) if errors else "OK")
