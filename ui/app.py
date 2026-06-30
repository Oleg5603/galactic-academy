import sys
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pdf_parser import load_pdf, extract_paragraphs
from ai_analyzer import analyze_chapter, ask_character, CHARACTERS
from tts.voice import speak, play

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

CHAR_COLORS = {
    "yoda":  "#2d8a4e",
    "vader": "#8b0000",
    "r2d2":  "#1a5276",
    "c3po":  "#b7950b",
    "obi":   "#1a3a6b",
}


class GalacticAcademy(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("⭐ Galactic Academy")
        self.geometry("1200x800")
        self.chapters = []
        self.current_chapter = 0
        self.analysis = {}
        self._build_ui()

    def _build_ui(self):
        # Верхняя панель
        top = ctk.CTkFrame(self, height=60)
        top.pack(fill="x", padx=10, pady=(10, 0))

        ctk.CTkButton(top, text="📂 Загрузить PDF", command=self._load_pdf, width=160).pack(side="left", padx=10, pady=10)
        self.title_label = ctk.CTkLabel(top, text="Загрузите учебник...", font=("Arial", 16, "bold"))
        self.title_label.pack(side="left", padx=20)

        # Нижняя панель — ответ персонажа (пакуем ДО main, иначе expand=True выталкивает за экран)
        self.response_frame = ctk.CTkFrame(self, height=240)
        self.response_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        self.response_frame.pack_propagate(False)

        self.char_name_label = ctk.CTkLabel(self.response_frame, text="", font=("Arial", 13, "bold"))
        self.char_name_label.pack(anchor="w", padx=15, pady=(8, 0))
        self.response_text = ctk.CTkTextbox(self.response_frame, height=130, wrap="word",
                                             font=("Arial", 12))
        self.response_text.pack(fill="x", padx=10, pady=(5, 0))

        q_frame = ctk.CTkFrame(self.response_frame)
        q_frame.pack(fill="x", padx=10, pady=8)
        self.question_entry = ctk.CTkEntry(q_frame, placeholder_text="Задай вопрос персонажу...",
                                            height=36, font=("Arial", 13))
        self.question_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.active_char = "yoda"
        ctk.CTkButton(q_frame, text="Спросить", command=self._ask_question,
                      width=110, height=36).pack(side="left")
        ctk.CTkButton(q_frame, text="⏹", command=self._stop_voice,
                      width=36, height=36, fg_color="#555555", hover_color="#333333").pack(side="left", padx=(6, 0))
        self.question_entry.bind("<Return>", lambda e: self._ask_question())

        # Основная область
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Левая панель — навигация
        left = ctk.CTkFrame(main, width=220)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="📚 Главы", font=("Arial", 14, "bold")).pack(pady=10)
        self.chapter_list = tk.Listbox(left, bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                                        font=("Arial", 11), borderwidth=0)
        self.chapter_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.chapter_list.bind("<<ListboxSelect>>", self._on_chapter_select)

        # Центр — текст
        center = ctk.CTkFrame(main)
        center.pack(side="left", fill="both", expand=True)

        # Анализ вверху
        self.analysis_frame = ctk.CTkFrame(center, height=120)
        self.analysis_frame.pack(fill="x", padx=5, pady=(5, 0))
        self.analysis_frame.pack_propagate(False)
        self.goal_label = ctk.CTkLabel(self.analysis_frame, text="", wraplength=600,
                                        font=("Arial", 13), justify="left")
        self.goal_label.pack(anchor="w", padx=10, pady=5)
        self.keys_label = ctk.CTkLabel(self.analysis_frame, text="", wraplength=600,
                                        font=("Arial", 11), text_color="#aaaaaa", justify="left")
        self.keys_label.pack(anchor="w", padx=10)

        # Текст главы
        self.text_box = tk.Text(center, wrap="word", bg="#1c1c1c", fg="#e0e0e0",
                                 font=("Arial", 13), padx=15, pady=15, borderwidth=0,
                                 selectbackground="#2a5a8a", state="disabled", cursor="arrow")
        self.text_box.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_box.tag_config("highlight", background="#3a5a2a", foreground="#90ee90")

        # Правая панель — персонажи
        right = ctk.CTkFrame(main, width=200)
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)

        ctk.CTkLabel(right, text="👾 Эксперты", font=("Arial", 14, "bold")).pack(pady=4)
        for char_id, char in CHARACTERS.items():
            btn = ctk.CTkButton(
                right, text=f"{char['emoji']} {char['name']}",
                fg_color=CHAR_COLORS[char_id],
                hover_color=CHAR_COLORS[char_id],
                command=lambda c=char_id: self._ask_expert(c),
                width=180, height=40
            )
            btn.pack(padx=10, pady=(3, 0))
            ctk.CTkLabel(
                right, text=char.get("hint", ""),
                font=("Arial", 10), text_color="#888888"
            ).pack(pady=(1, 2))


    def _load_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF файлы", "*.pdf")])
        if not path:
            return
        self.title_label.configure(text="⏳ Загружаю...")
        self.update()
        self.chapters = load_pdf(path)
        self.chapter_list.delete(0, "end")
        for i, ch in enumerate(self.chapters):
            self.chapter_list.insert("end", f"  {i+1}. {ch['title'][:30]}")
        name = os.path.basename(path)
        self.title_label.configure(text=f"📖 {name} — {len(self.chapters)} глав")
        if self.chapters:
            self.chapter_list.select_set(0)
            self._show_chapter(0)

    def _on_chapter_select(self, event):
        sel = self.chapter_list.curselection()
        if sel:
            self._show_chapter(sel[0])

    def _show_chapter(self, idx):
        self.current_chapter = idx
        ch = self.chapters[idx]
        self.text_box.config(state="normal")
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", ch["text"])
        self.text_box.config(state="disabled")
        self.goal_label.configure(text="⏳ Анализирую...")
        self.update()
        threading.Thread(target=self._analyze_bg, args=(ch,), daemon=True).start()

    def _analyze_bg(self, ch):
        self.analysis = analyze_chapter(ch["text"])
        self.after(0, self._show_analysis)

    def _show_analysis(self):
        goal = self.analysis.get("goal", "")
        keys = self.analysis.get("keywords", [])
        points = self.analysis.get("key_points", [])
        self.goal_label.configure(text=f"🎯 {goal}")
        self.keys_label.configure(text="🔑 " + " • ".join(keys))
        self._highlight_keywords(keys)

    def _highlight_keywords(self, keywords):
        self.text_box.config(state="normal")
        self.text_box.tag_remove("highlight", "1.0", "end")
        for word in keywords:
            start = "1.0"
            while True:
                pos = self.text_box.search(word, start, stopindex="end", nocase=True)
                if not pos:
                    break
                end = f"{pos}+{len(word)}c"
                self.text_box.tag_add("highlight", pos, end)
                start = end
        self.text_box.config(state="disabled")

    def _ask_expert(self, char_id: str):
        if not self.chapters:
            messagebox.showwarning("Нет PDF", "Сначала загрузи PDF через кнопку вверху!")
            return
        self.active_char = char_id
        char = CHARACTERS[char_id]
        self.char_name_label.configure(text=f"{char['emoji']} {char['name']} говорит:")
        try:
            sel = self.text_box.tag_ranges("sel")
            text = self.text_box.get(sel[0], sel[1]) if sel else self.chapters[self.current_chapter]["text"]
        except Exception:
            text = self.chapters[self.current_chapter]["text"]
        self.response_text.delete("1.0", "end")
        self.response_text.insert("1.0", "⏳ Думаю...")
        threading.Thread(target=self._get_response_bg, args=(char_id, text, ""), daemon=True).start()

    def _ask_question(self):
        q = self.question_entry.get().strip()
        if not q:
            return
        text = self.chapters[self.current_chapter]["text"] if self.chapters else ""
        self.response_text.delete("1.0", "end")
        self.response_text.insert("1.0", "⏳ Думаю...")
        threading.Thread(target=self._get_response_bg, args=(self.active_char, text, q), daemon=True).start()

    def _get_response_bg(self, char_id, text, question):
        try:
            response = ask_character(char_id, text, question)
        except Exception as e:
            response = f"⚠️ Ошибка: {e}"
        self.after(0, lambda: self._show_response(response, char_id))

    def _show_response(self, response, char_id):
        self.response_text.delete("1.0", "end")
        self.response_text.insert("1.0", response)
        char = CHARACTERS[char_id]
        # Простое надёжное окно
        win = tk.Toplevel(self)
        win.title(f"{char['emoji']} {char['name']}")
        win.geometry("620x420")
        win.attributes("-topmost", True)
        win.configure(bg="#1c1c1c")
        tk.Label(win, text=f"{char['emoji']} {char['name']}", bg="#1c1c1c", fg="white",
                 font=("Arial", 14, "bold")).pack(pady=10)
        txt = tk.Text(win, wrap="word", bg="#2b2b2b", fg="#e0e0e0",
                      font=("Arial", 13), padx=12, pady=12, borderwidth=0)
        txt.pack(fill="both", expand=True, padx=10)
        txt.insert("1.0", response)
        txt.config(state="disabled")
        tk.Button(win, text="Закрыть", command=win.destroy,
                  bg="#1f6aa5", fg="white", font=("Arial", 12),
                  relief="flat", padx=20, pady=6).pack(pady=10)
        threading.Thread(target=self._play_voice, args=(response, char_id), daemon=True).start()

    def _stop_voice(self):
        from tts.voice import stop
        stop()

    def _play_voice(self, text, char_id):
        try:
            path = speak(text, char_id)
            play(path)
        except Exception:
            pass


def main():
    app = GalacticAcademy()
    app.mainloop()


if __name__ == "__main__":
    main()
