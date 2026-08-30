"""
Wortschatz — приложение для изучения немецких слов.
Немецкий -> Русский, автоматический перевод через Google Translate,
хранение слов в локальной SQLite базе, категории: Новые / Учу / Выучено.
 
Запуск: python wortschatz.py
Перед первым запуском один раз установить библиотеку перевода:
    pip install deep-translator
"""
 
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
 
try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None
 
# Если приложение собрано через PyInstaller (.exe) — __file__ указывает на временную
# папку распаковки, которая меняется при каждом запуске. Поэтому в таком случае берём
# папку, где реально лежит сам .exe (sys.executable), а не временную.
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
 
DB_PATH = os.path.join(APP_DIR, "wortschatz.db")
 
CATEGORIES = ["Новые", "Учу", "Выучено"]
 
 
# ---------- База данных ----------
 
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            de TEXT NOT NULL,
            ru TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Новые'
        )
    """)
    conn.commit()
    conn.close()
 
 
def add_word(de, ru, category="Новые"):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO words (de, ru, category) VALUES (?, ?, ?)", (de, ru, category))
    conn.commit()
    conn.close()
 
 
def get_words(category):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, de, ru FROM words WHERE category = ? ORDER BY de", (category,))
    rows = cur.fetchall()
    conn.close()
    return rows
 
 
def delete_word(word_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM words WHERE id = ?", (word_id,))
    conn.commit()
    conn.close()
 
 
def move_word(word_id, new_category):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE words SET category = ? WHERE id = ?", (new_category, word_id))
    conn.commit()
    conn.close()
 
 
def word_exists(de):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM words WHERE LOWER(de) = LOWER(?)", (de,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists
 
 
# ---------- Перевод ----------
 
def translate_de_to_ru(word):
    if GoogleTranslator is None:
        raise RuntimeError("Библиотека deep-translator не установлена. Выполни: pip install deep-translator")
    return GoogleTranslator(source="de", target="ru").translate(word)
 
 
# ---------- Интерфейс ----------
 
class WortschatzApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wortschatz — немецкий словарь")
        self.geometry("520x480")
        self.resizable(False, False)
 
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)
 
        self.add_tab = AddWordTab(notebook, on_word_added=self.refresh_dictionary)
        self.dict_tab = DictionaryTab(notebook)
 
        notebook.add(self.add_tab, text="Добавить слово")
        notebook.add(self.dict_tab, text="Словарь")
 
    def refresh_dictionary(self):
        self.dict_tab.refresh_all()
 
 
class AddWordTab(ttk.Frame):
    def __init__(self, parent, on_word_added):
        super().__init__(parent)
        self.on_word_added = on_word_added
 
        ttk.Label(self, text="Введи немецкое слово:", font=("Segoe UI", 11)).pack(pady=(30, 8))
 
        self.entry = ttk.Entry(self, width=30, font=("Segoe UI", 12))
        self.entry.pack(pady=4)
        self.entry.bind("<Return>", lambda event: self.handle_add())
        self.entry.focus()
 
        ttk.Button(self, text="Перевести и добавить", command=self.handle_add).pack(pady=10)
 
        self.result_label = ttk.Label(self, text="", font=("Segoe UI", 11, "italic"))
        self.result_label.pack(pady=10)
 
    def handle_add(self):
        word = self.entry.get().strip()
        if not word:
            return
 
        if word_exists(word):
            messagebox.showinfo("Уже есть", f'Слово "{word}" уже есть в словаре.')
            return
 
        try:
            translation = translate_de_to_ru(word)
        except Exception as e:
            messagebox.showerror("Ошибка перевода", str(e))
            return
 
        add_word(word, translation, category="Новые")
        self.result_label.config(text=f"{word} → {translation}  (добавлено в «Новые»)")
        self.entry.delete(0, tk.END)
        self.entry.focus()
        self.on_word_added()
 
 
class DictionaryTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
 
        self.category_tabs = {}
        inner_notebook = ttk.Notebook(self)
        inner_notebook.pack(fill="both", expand=True, padx=4, pady=4)
 
        for category in CATEGORIES:
            frame = CategoryFrame(inner_notebook, category, self)
            inner_notebook.add(frame, text=category)
            self.category_tabs[category] = frame
 
    def refresh_all(self):
        for frame in self.category_tabs.values():
            frame.refresh()
 
 
class CategoryFrame(ttk.Frame):
    def __init__(self, parent, category, dictionary_tab):
        super().__init__(parent)
        self.category = category
        self.dictionary_tab = dictionary_tab
 
        columns = ("de", "ru")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        self.tree.heading("de", text="Немецкий")
        self.tree.heading("ru", text="Русский")
        self.tree.column("de", width=200)
        self.tree.column("ru", width=200)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)
 
        button_row = ttk.Frame(self)
        button_row.pack(fill="x", padx=6, pady=(0, 6))
 
        ttk.Button(button_row, text="Удалить", command=self.handle_delete).pack(side="left", padx=4)
 
        self.move_target = tk.StringVar()
        other_categories = [c for c in CATEGORIES if c != self.category]
        self.move_target.set(other_categories[0])
        move_dropdown = ttk.Combobox(button_row, textvariable=self.move_target,
                                      values=other_categories, width=12, state="readonly")
        move_dropdown.pack(side="left", padx=4)
 
        ttk.Button(button_row, text="Переместить", command=self.handle_move).pack(side="left", padx=4)
 
        self.refresh()
 
    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for word_id, de, ru in get_words(self.category):
            self.tree.insert("", tk.END, iid=str(word_id), values=(de, ru))
 
    def get_selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Выбери слово", "Сначала выбери слово в списке.")
            return None
        return int(selection[0])
 
    def handle_delete(self):
        word_id = self.get_selected_id()
        if word_id is None:
            return
        delete_word(word_id)
        self.refresh()
 
    def handle_move(self):
        word_id = self.get_selected_id()
        if word_id is None:
            return
        move_word(word_id, self.move_target.get())
        self.refresh()
        self.dictionary_tab.refresh_all()
 
 
if __name__ == "__main__":
    init_db()
    app = WortschatzApp()
    app.mainloop()
