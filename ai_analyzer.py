import os
import re
import json as _json
import requests as _req

def _spellfix(text: str) -> str:
    return text

_API_URL   = "https://openrouter.ai/api/v1/chat/completions"
_API_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
_API_KEY   = ""  # задаётся через OPENROUTER_API_KEY в .env

_session = _req.Session()

_LANG_RULE = "\nОтвечай по-русски."


def _llm(system: str, user: str, max_tokens: int = 400) -> str:
    import time
    key = os.getenv("OPENROUTER_API_KEY", "") or _API_KEY
    payload = {
        "model": _API_MODEL, "max_tokens": max_tokens,
        "messages": [{"role": "system", "content": system + _LANG_RULE},
                     {"role": "user", "content": user}],
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for attempt in range(4):
        r = _session.post(_API_URL, headers=headers, json=payload, timeout=40)
        if r.status_code == 429:
            time.sleep([12, 20, 30, 40][attempt])
            continue
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"API [{r.status_code}]: {data['error'].get('message', str(data['error']))}")
        if "choices" not in data or not data["choices"]:
            raise RuntimeError(f"Нет ответа: {str(data)[:200]}")
        return data["choices"][0]["message"]["content"]
    raise RuntimeError("Превышен лимит запросов (429). Подождите минуту.")


CHARACTERS = {
    "yoda": {
        "name": "Мастер Йода", "emoji": "🟢", "hint": "3-5 ключевых тезиса",
        "prompt": "Мастер Йода. Инверсия слов, мудрость, краткость. 3-5 тезисов из текста, каждый с '→'.",
    },
    "vader": {
        "name": "Дарт Вейдер", "emoji": "⚫", "hint": "3 вопроса для проверки",
        "prompt": "Дарт Вейдер. Угрожающий тон. 3 вопроса проверки понимания текста, затем 'ОТВЕТЫ:' с ответами.",
    },
    "r2d2": {
        "name": "R2-D2", "emoji": "🔵", "hint": "Сложное — простыми словами",
        "prompt": "R2-D2 с переводчиком. 2-3 сложных момента текста с '⚡ СЛОЖНЫЙ МОМЕНТ:'. Аналогии из жизни.",
    },
    "c3po": {
        "name": "C-3PO", "emoji": "🟡", "hint": "Термины и определения",
        "prompt": "C-3PO, протокольный дроид. Термины из текста: '📖 ТЕРМИН → определение → простыми словами'.",
    },
    "obi": {
        "name": "Оби-Ван Кеноби", "emoji": "🔵", "hint": "Зачем это в жизни",
        "prompt": "Оби-Ван Кеноби. Мудрый наставник. Объясни связь текста с реальной жизнью, с примерами.",
    },
}

# Батч-промпт для дебатов: один запрос вместо пяти
_DEBATE_SYSTEM = """\
Четыре персонажа Звёздных войн обсуждают учебный текст (2-3 предложения каждый):
- yoda: Мастер Йода — инверсия слов, мудрость, что важно/не важно в тексте
- vader: Дарт Вейдер — угроза, жёсткость, укажи слабое место текста
- r2d2: R2-D2 — факты и данные, что правда, что спорно, без эмоций
- c3po: C-3PO — педантизм, точность терминов, где обычно ошибаются
- obi: Оби-Ван Кеноби — мудрое резюме дебатов, 2-3 предложения итога
Верни ТОЛЬКО JSON без markdown: {"yoda":"...","vader":"...","r2d2":"...","c3po":"...","obi":"..."}\
"""


def debate_all(text: str) -> dict:
    """Один API-вызов для всех 5 участников дебатов. Возвращает {char_id: ответ}."""
    raw = _llm(_DEBATE_SYSTEM, f"ТЕКСТ:\n{text[:700]}", max_tokens=700)
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return _json.loads(match.group())
        except Exception:
            pass
    return {}


def analyze_chapter(text: str) -> dict:
    try:
        raw = _llm(
            "Учебный ассистент. Только JSON без пояснений.",
            f'JSON: {{"goal":"цель","key_points":["т1","т2","т3"],"keywords":["с1","с2","с3","с4","с5"]}}\nТЕКСТ:\n{text[:1200]}',
        )
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return _json.loads(match.group())
    except Exception:
        pass
    return _analyze_local(text)


def _analyze_local(text: str) -> dict:
    from collections import Counter
    words = re.findall(r'[а-яёА-ЯЁa-zA-Z]{5,}', text)
    stop = {"этого","этом","этот","которые","который","которая","более","также",
            "можно","нужно","такие","такой","после","через","между","очень",
            "когда","потому","будет","может","всего","своей","своего","своих"}
    freq = Counter(w.lower() for w in words if w.lower() not in stop)
    keywords = [w for w, _ in freq.most_common(7)]
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 40]
    goal = sentences[0][:120] if sentences else "Изучить материал"
    return {"goal": goal, "key_points": sentences[1:4], "keywords": keywords}


def ask_character(character_id: str, text: str, question: str = "", debate: bool = False) -> str:
    char = CHARACTERS.get(character_id, CHARACTERS["yoda"])
    prompt = char["prompt"]
    user_msg = f"ТЕКСТ:\n{text[:700]}"
    if question:
        user_msg += f"\nВОПРОС: {question}"
    try:
        return _llm(prompt, user_msg, max_tokens=350)
    except Exception as e:
        return f"⚠️ Ошибка: {str(e)[:250]}"


def summarize_debate(text: str, responses: dict) -> str:
    debate = "\n".join(
        f"{CHARACTERS[cid]['name']}: {resp}"
        for cid, resp in responses.items() if cid in CHARACTERS
    )
    system = "Оби-Ван Кеноби. Краткое резюме дебатов (3 предложения): что важно, где сошлись/разошлись."
    try:
        return _llm(system, f"ТЕКСТ:\n{text[:500]}\nДЕБАТЫ:\n{debate[:1500]}", max_tokens=300)
    except Exception as e:
        return f"⚠️ Ошибка резюме: {str(e)[:200]}"
