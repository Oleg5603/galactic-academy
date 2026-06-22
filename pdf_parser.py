import fitz  # PyMuPDF
import re


def load_pdf(path: str) -> list[dict]:
    """Загружает PDF и возвращает список глав с текстом."""
    doc = fitz.open(path)
    chapters = []
    current = {"title": "Введение", "text": "", "page_start": 1}

    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if _is_chapter_header(line):
                if current["text"].strip():
                    chapters.append(current)
                current = {"title": line, "text": "", "page_start": page_num}
            else:
                current["text"] += line + " "

    if current["text"].strip():
        chapters.append(current)

    doc.close()
    return chapters


def _is_chapter_header(line: str) -> bool:
    patterns = [
        r"^(Глава|Chapter|ГЛАВА|Раздел|§)\s+\d+",
        r"^\d+\.\s+[А-ЯA-Z]",
        r"^[А-ЯA-Z\s]{5,40}$",
    ]
    return any(re.match(p, line) for p in patterns)


def extract_paragraphs(chapter_text: str, min_len: int = 100) -> list[str]:
    """Делит текст главы на абзацы."""
    parts = [p.strip() for p in chapter_text.split("  ") if len(p.strip()) >= min_len]
    return parts if parts else [chapter_text]
