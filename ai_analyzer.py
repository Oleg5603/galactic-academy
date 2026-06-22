import anthropic
import httpx
from httpx_socks import SyncProxyTransport
import os

_transport = SyncProxyTransport.from_url("socks4://127.0.0.1:10808")
_http = httpx.Client(transport=_transport, timeout=30)
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    http_client=_http,
)

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
    """Йода анализирует главу: цель, ключевые моменты, доп. инфо."""
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": (
                f"Проанализируй учебный текст и верни JSON:\n"
                f'{{"goal": "цель урока одним предложением", '
                f'"key_points": ["тезис1", "тезис2", "тезис3"], '
                f'"keywords": ["слово1", "слово2", "слово3", "слово4", "слово5"]}}\n\n'
                f"ТЕКСТ:\n{text[:3000]}"
            )
        }]
    )
    import json, re
    raw = msg.content[0].text
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {"goal": "Изучить материал", "key_points": [], "keywords": []}


def ask_character(character_id: str, text: str, question: str = "") -> str:
    """Персонаж отвечает на вопрос по тексту."""
    char = CHARACTERS.get(character_id, CHARACTERS["yoda"])
    user_msg = f"ТЕКСТ ПАРАГРАФА:\n{text[:2000]}"
    if question:
        user_msg += f"\n\nВОПРОС СТУДЕНТА: {question}"

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        system=char["prompt"],
        messages=[{"role": "user", "content": user_msg}]
    )
    return msg.content[0].text
