import httpx
import os
import json as _json

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

_http = httpx.Client(trust_env=False, timeout=30)


def _groq(system: str, user: str, max_tokens: int = 600) -> str:
    r = _http.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": GROQ_MODEL, "max_tokens": max_tokens,
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": user}]},
    )
    return r.json()["choices"][0]["message"]["content"]

CHARACTERS = {
    "yoda": {
        "name": "Мастер Йода",
        "emoji": "🟢",
        "prompt": (
            "Ты — Мастер Йода. Говоришь как Йода: инверсия слов, мудрость, краткость. "
            "Выдели ТОЛЬКО 3-5 ключевых тезиса из текста. Каждый начинай с '→'. "
            "Лишнего не говори. Только суть."
        ),
    },
    "vader": {
        "name": "Дарт Вейдер",
        "emoji": "⚫",
        "prompt": (
            "Ты — Дарт Вейдер. Требовательно, с угрозой, но по делу. "
            "Задай 3 вопроса для проверки понимания текста. "
            "Начинай каждый вопрос с нового абзаца. После вопросов добавь правильные ответы под 'ОТВЕТЫ:'."
        ),
    },
    "r2d2": {
        "name": "R2-D2",
        "emoji": "🔵",
        "prompt": (
            "Ты — R2-D2 с переводчиком. Найди 2-3 самых сложных момента в тексте "
            "и объясни каждый ОЧЕНЬ простыми словами. Начинай каждый с '⚡ СЛОЖНЫЙ МОМЕНТ:'. "
            "Используй аналогии из жизни."
        ),
    },
    "c3po": {
        "name": "C-3PO",
        "emoji": "🟡",
        "prompt": (
            "Ты — C-3PO, протокольный дроид. Вежливо и многословно объясни основные термины "
            "и понятия из текста. Для каждого термина: сначала официальное определение, "
            "затем простое объяснение. Формат: '📖 ТЕРМИН → определение → простыми словами'."
        ),
    },
    "obi": {
        "name": "Оби-Ван Кеноби",
        "emoji": "🔵",
        "prompt": (
            "Ты — Оби-Ван Кеноби. Мудро и с перспективой объясни КАК этот материал "
            "связан с реальной жизнью и зачем его знать. Дай исторический контекст если уместно. "
            "Стиль: наставник, не спеша, с примерами."
        ),
    },
}


def analyze_chapter(text: str) -> dict:
    """Анализирует главу через Groq, при ошибке — локально."""
    if not GROQ_API_KEY:
        return _analyze_local(text)
    try:
        import re
        raw = _groq(
            "Ты учебный ассистент. Отвечай только JSON без пояснений.",
            f'Проанализируй текст и верни JSON:\n{{"goal":"цель одним предложением","key_points":["тезис1","тезис2","тезис3"],"keywords":["слово1","слово2","слово3","слово4","слово5"]}}\n\nТЕКСТ:\n{text[:2000]}',
            800
        )
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return _json.loads(match.group())
    except Exception:
        pass
    return _analyze_local(text)


def _analyze_local(text: str) -> dict:
    """Локальный анализ без API — частотные слова."""
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
    """Персонаж отвечает на вопрос по тексту."""
    char = CHARACTERS.get(character_id, CHARACTERS["yoda"])
    if not GROQ_API_KEY:
        return "⚠️ Добавь GROQ_API_KEY в файл .env\nБесплатный ключ: console.groq.com"
    user_msg = f"ТЕКСТ ПАРАГРАФА:\n{text[:2000]}"
    if question:
        user_msg += f"\n\nВОПРОС СТУДЕНТА: {question}"
    try:
        return _groq(char["prompt"], user_msg, 600)
    except Exception as e:
        return f"⚠️ Ошибка: {str(e)[:150]}"
