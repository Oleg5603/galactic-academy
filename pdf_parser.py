import fitz  # PyMuPDF
import re


def load_pdf(path: str) -> list[dict]:
    """Загружает PDF и возвращает список глав с текстом."""
    doc = fitz.open(path)
    total_pages = len(doc)
    chapters = []
    current = {"title": "Введение", "text": "", "page_start": 1, "_pdf_path": path}

    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if _is_chapter_header(line):
                if current["text"].strip():
                    current["page_end"] = page_num - 1
                    chapters.append(current)
                current = {"title": line, "text": "", "page_start": page_num, "_pdf_path": path}
            else:
                current["text"] += line + " "

    if current["text"].strip():
        current["page_end"] = total_pages
        chapters.append(current)

    doc.close()
    return chapters


def extract_chapter_images(pdf_path: str, page_start: int, page_end: int,
                            max_pages: int = 30) -> list[bytes]:
    """Рендерит страницы главы как PNG. Работает с любым PDF, включая векторную графику."""
    doc = fitz.open(pdf_path)
    images = []
    mat = fitz.Matrix(120 / 72, 120 / 72)   # 120 DPI — читаемо, не тяжело
    end = min(page_end, len(doc), page_start - 1 + max_pages)
    for page_num in range(page_start - 1, end):
        pix = doc[page_num].get_pixmap(matrix=mat, alpha=False)
        images.append(pix.tobytes("png"))
        pix = None
    doc.close()
    return images


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
