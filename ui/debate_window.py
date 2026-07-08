import tkinter as tk
import threading

from ai_analyzer import debate_all, CHARACTERS

CHAR_ORDER = ["yoda", "vader", "r2d2", "c3po"]

CHAR_COLORS = {
    "yoda":  "#2d8a4e",
    "vader": "#8b0000",
    "r2d2":  "#1a5276",
    "c3po":  "#b7950b",
    "obi":   "#1a3a6b",
}


def open_debate(parent, text: str):
    win = tk.Toplevel(parent)
    win.title("⚔️ Галактические Дебаты")
    win.geometry("780x700")
    win.configure(bg="#1c1c1c")
    win.attributes("-topmost", True)

    outer = tk.Frame(win, bg="#1c1c1c")
    outer.pack(fill="both", expand=True, padx=8, pady=8)

    canvas = tk.Canvas(outer, bg="#1c1c1c", highlightthickness=0)
    scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="#1c1c1c")

    scroll_frame.bind("<Configure>",
                      lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=740)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    canvas.bind_all("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-1 * e.delta / 120), "units"))

    response_widgets: dict[str, tk.Text] = {}

    for char_id in CHAR_ORDER:
        char = CHARACTERS[char_id]
        color = CHAR_COLORS[char_id]
        block = tk.Frame(scroll_frame, bg="#252525", padx=2, pady=2)
        block.pack(fill="x", padx=4, pady=4)
        tk.Label(block, text=f"{char['emoji']} {char['name']}",
                 bg=color, fg="white", font=("Arial", 12, "bold"),
                 anchor="w", padx=10, pady=5).pack(fill="x")
        body = tk.Text(block, wrap="word", bg="#2b2b2b", fg="#dddddd",
                       font=("Arial", 12), padx=10, pady=8, height=3, borderwidth=0)
        body.insert("1.0", "⏳ думает...")
        body.config(state="disabled")
        body.pack(fill="x")
        response_widgets[char_id] = body

    tk.Label(scroll_frame, text="─" * 80, bg="#1c1c1c",
             fg="#444444", font=("Arial", 9)).pack(fill="x", pady=(10, 2))
    tk.Label(scroll_frame, text="🔵 Оби-Ван Кеноби — резюме дебатов",
             bg="#1a3a6b", fg="white", font=("Arial", 12, "bold"),
             anchor="w", padx=10, pady=5).pack(fill="x", padx=4)
    obi_body = tk.Text(scroll_frame, wrap="word", bg="#1e2d4a", fg="#c8d8f0",
                       font=("Arial", 12, "italic"), padx=10, pady=10,
                       height=5, borderwidth=0)
    obi_body.insert("1.0", "⏳ Жду ответов участников...")
    obi_body.config(state="disabled")
    obi_body.pack(fill="x", padx=4, pady=(0, 10))

    tk.Button(win, text="Закрыть", command=win.destroy,
              bg="#444444", fg="white", font=("Arial", 11),
              relief="flat", padx=20, pady=6).pack(pady=(0, 8))

    def _set_text(widget: tk.Text, text: str):
        lines = max(3, min(18, text.count("\n") + len(text) // 70 + 1))
        widget.config(state="normal", height=lines)
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        win.update_idletasks()
        widget.config(state="disabled")
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _worker():
        try:
            results = debate_all(text)
        except Exception as e:
            results = {cid: f"⚠️ {e}" for cid in CHAR_ORDER}
            results["obi"] = f"⚠️ {e}"

        def _apply():
            if not win.winfo_exists():
                return
            for char_id in CHAR_ORDER:
                resp = results.get(char_id, "⚠️ Нет ответа")
                _set_text(response_widgets[char_id], resp)
            _set_text(obi_body, results.get("obi", "⚠️ Нет резюме"))

        win.after(0, _apply)

    threading.Thread(target=_worker, daemon=True).start()
