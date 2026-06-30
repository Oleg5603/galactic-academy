import os
import re
import json as _json
import requests as _req

def _spellfix(text: str) -> str:
    """Исправляет очевидные орфографические ошибки в русском тексте."""
    try:
        from spellchecker import SpellChecker
        spell = SpellChecker(language="ru")
        def fix_word(m):
            w = m.group(0)
            if not re.search(r'[а-яёА-ЯЁ]', w):
                return w
            lower = w.lower()
            correction = spell.correction(lower)
            if correction and correction != lower:
                return correction[0].upper() + correction[1:] if w[0].isupper() else correction
            return w
        return re.sub(r'\b[а-яёА-ЯЁ]{3,}\b', fix_word, text)
    except Exception:
        return text

_API_URL = "https://openrouter.ai/api/v1/chat/completions"
_API_MODEL = "openrouter/free"
_API_KEY = ""  # задаётся через OPENROUTER_API_KEY в .env

# Сессия с автодетектом системного прокси (VPN/прокси на ПК)
_session = _req.Session()


_LANG_RULE = "\n\nОБЯЗАТЕЛЬНО: отвечай только на грамотном русском языке, без опечаток и ошибок."


def _llm(system: str, user: str, max_tokens: int = 800) -> str:
    key = os.getenv("OPENROUTER_API_KEY", "") or _API_KEY
    r = _session.post(
        _API_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": _API_MODEL, "max_tokens": max_tokens,
              "messages": [{"role": "system", "content": system + _LANG_RULE},
                           {"role": "user", "content": user}]},
        timeout=30,
    )
    data = r.json()
    if "error" in data:
        msg = data["error"].get("message", str(data["error"]))
        raise RuntimeError(f"API [{r.status_code}]: {msg}")
    if "choices" not in data or not data["choices"]:
        raise RuntimeError(f"Нет ответа: {str(data)[:200]}")
    return data["choices"][0]["message"]["content"]


CHARACTERS = {
    "yoda": {
        "name": "Мастер Йода",
        "emoji": "🟢",
        "hint": "3-5 ключевых тезиса",
        "prompt": (
            "Ты — Мастер Йода. Говоришь как Йода: инверсия слов, мудрость, краткость. "
            "Выдели ТОЛЬКО 3-5 ключевых тезиса из текста. Каждый начинай с '→'. "
            "Лишнего не говори. Только суть."
        ),
    },
    "vader": {
        "name": "Дарт Вейдер",
        "emoji": "⚫",
        "hint": "3 вопроса для проверки",
        "prompt": (
            "Ты — Дарт Вейдер. Требовательно, с угрозой, но по делу. "
            "Задай 3 вопроса для проверки понимания текста. "
            "Начинай каждый вопрос с нового абзаца. После вопросов добавь правильные ответы под 'ОТВЕТЫ:'."
        ),
    },
    "r2d2": {
        "name": "R2-D2",
        "emoji": "🔵",
        "hint": "Сложное — простыми словами",
        "prompt": (
            "Ты — R2-D2 с переводчиком. Найди 2-3 самых сложных момента в тексте "
            "и объясни каждый ОЧЕНЬ простыми словами. Начинай каждый с '⚡ СЛОЖНЫЙ МОМЕНТ:'. "
            "Используй аналогии из жизни."
        ),
    },
    "c3po": {
        "name": "C-3PO",
        "emoji": "🟡",
        "hint": "Термины и определения",
        "prompt": (
            "Ты — C-3PO, протокольный дроид. Вежливо и многословно объясни основные термины "
            "и понятия из текста. Для каждого термина: сначала официальное определение, "
            "затем простое объяснение. Формат: '📖 ТЕРМИН → определение → простыми словами'."
        ),
    },
    "obi": {
        "name": "Оби-Ван Кеноби",
        "emoji": "🔵",
        "hint": "Зачем это в жизни",
        "prompt": (
            "Ты — Оби-Ван Кеноби. Мудро и с перспективой объясни КАК этот материал "
            "связан с реальной жизнью и зачем его знать. Дай исторический контекст если уместно. "
            "Стиль: наставник, не спеша, с примерами."
        ),
    },
}


def analyze_chapter(text: str) -> dict:
    try:
        import re
        raw = _llm(
            "Ты учебный ассистент. Отвечай только JSON без пояснений.",
            f'Проанализируй текст и верни JSON:\n{{"goal":"цель одним предложением","key_points":["тезис1","тезис2","тезис3"],"keywords":["слово1","слово2","слово3","слово4","слово5"]}}\n\nТЕКСТ:\n{text[:2000]}',
        )
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return _json.loads(match.group())
    except Exception:
        pass
    return _analyze_local(text)


def _analyze_local(text: str) -> dict:
    import re
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


def ask_character(character_id: str, text: str, question: str = "") -> str:
    char = CHARACTERS.get(character_id, CHARACTERS["yoda"])
    user_msg = f"ТЕКСТ ПАРАГРАФА:\n{text[:2000]}"
    if question:
        user_msg += f"\n\nВОПРОС СТУДЕНТА: {question}"
    try:
        return _spellfix(_llm(char["prompt"], user_msg))
    except Exception as e:
        return f"⚠️ Ошибка: {str(e)[:250]}"
