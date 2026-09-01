"""
Wortschatz is an app for learning German words.
German -> Russian, automatic translation via Google Translate,
word storage in a local SQLite database, categories: New / Learning / Learned.

Run: python wortschatz.py
Before the first run, install the translation library once:
pip install deep-translator
"""
import sqlite3
import time
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import random

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

# Внутренние (хранимые в базе) названия категорий — НЕ переводятся, чтобы не
# ломать уже сохранённые данные. Переводятся только подписи, которые видит
# пользователь (см. TEXTS[...]["categories"]).
CATEGORIES = ["Новые", "Учу", "Выучено"]
LEARNING_CATEGORY = "Учу"
LEARNED_CATEGORY = "Выучено"

# Сколько раз автоматически повторять попытку перевода, прежде чем показать
# пользователю ошибку (перевод иногда "барахлит" с первого раза).
TRANSLATE_RETRIES = 3
TRANSLATE_RETRY_DELAY = 0.6  # секунды между попытками


# ---------- Переводы интерфейса ----------

TEXTS = {
    "ru": {
        "window_title": "Wortschatz — немецкий словарь",
        "tab_add": "Добавить слово",
        "tab_dictionary": "Словарь",
        "tab_flashcards": "Карточки",
        "add_prompt": "Введи немецкое слово:",
        "add_button": "Перевести и добавить",
        "added_suffix": "(добавлено в «{cat}»)",
        "already_exists_title": "Уже есть",
        "already_exists_msg": 'Слово "{word}" уже есть в словаре.',
        "translate_error_title": "Ошибка перевода",
        "delete_button": "Удалить",
        "move_button": "Переместить",
        "select_word_title": "Выбери слово",
        "select_word_msg": "Сначала выбери слово в списке.",
        "col_de": "Немецкий",
        "col_ru": "Русский",
        "categories": {"Новые": "Новые", "Учу": "Учу", "Выучено": "Выучено"},
        "lang_label": "Язык интерфейса:",
        "flash_show_answer": "Показать перевод",
        "flash_next": "Следующее слово",
        "flash_empty": "В категории «Учу» пока нет слов для повторения.",
        "flash_progress": "Карточка {current} из {total}",
        "flash_intro": "Как переводится это слово?",
    },
    "en": {
        "window_title": "Wortschatz — German dictionary",
        "tab_add": "Add word",
        "tab_dictionary": "Dictionary",
        "tab_flashcards": "Flashcards",
        "add_prompt": "Type a German word:",
        "add_button": "Translate & add",
        "added_suffix": "(added to “{cat}”)",
        "already_exists_title": "Already exists",
        "already_exists_msg": 'The word "{word}" is already in the dictionary.',
        "translate_error_title": "Translation error",
        "delete_button": "Delete",
        "move_button": "Move",
        "select_word_title": "Select a word",
        "select_word_msg": "Please select a word in the list first.",
        "col_de": "German",
        "col_ru": "Russian",
        "categories": {"Новые": "New", "Учу": "Learning", "Выучено": "Learned"},
        "lang_label": "Interface language:",
        "flash_show_answer": "Show translation",
        "flash_next": "Next word",
        "flash_empty": "No words under “Learning” yet.",
        "flash_progress": "Card {current} of {total}",
        "flash_intro": "What does this word mean?",
    },
    "de": {
        "window_title": "Wortschatz — Deutsches Wörterbuch",
        "tab_add": "Wort hinzufügen",
        "tab_dictionary": "Wörterbuch",
        "tab_flashcards": "Karteikarten",
        "add_prompt": "Gib ein deutsches Wort ein:",
        "add_button": "Übersetzen & hinzufügen",
        "added_suffix": "(zu „{cat}“ hinzugefügt)",
        "already_exists_title": "Bereits vorhanden",
        "already_exists_msg": 'Das Wort "{word}" ist bereits im Wörterbuch.',
        "translate_error_title": "Übersetzungsfehler",
        "delete_button": "Löschen",
        "move_button": "Verschieben",
        "select_word_title": "Wort auswählen",
        "select_word_msg": "Bitte zuerst ein Wort in der Liste auswählen.",
        "col_de": "Deutsch",
        "col_ru": "Russisch",
        "categories": {"Новые": "Neu", "Учу": "Lernen", "Выучено": "Gelernt"},
        "lang_label": "Oberflächensprache:",
        "flash_show_answer": "Übersetzung zeigen",
        "flash_next": "Nächstes Wort",
        "flash_empty": "Noch keine Wörter unter „Lernen“.",
        "flash_progress": "Karte {current} von {total}",
        "flash_intro": "Was bedeutet dieses Wort?",
    },
}

LANG_NAMES = {"ru": "Русский", "en": "English", "de": "Deutsch"}
LANG_CODES_BY_NAME = {v: k for k, v in LANG_NAMES.items()}

# ---------- Темы оформления ----------

THEMES = {
    "light": {
        "bg": "#f0f0f0",
        "fg": "#1a1a1a",
        "field_bg": "#ffffff",
        "select_bg": "#0078d7",
        "select_fg": "#ffffff",
        "tree_bg": "#ffffff",
        "tree_fg": "#1a1a1a",
        "heading_bg": "#e1e1e1",
        "answer_color": "#2a6f2a",
        "toggle_icon": "🌙",
    },
    "dark": {
        "bg": "#2b2b2b",
        "fg": "#e6e6e6",
        "field_bg": "#3c3f41",
        "select_bg": "#3a6ea5",
        "select_fg": "#ffffff",
        "tree_bg": "#2b2b2b",
        "tree_fg": "#e6e6e6",
        "heading_bg": "#3c3f41",
        "answer_color": "#7fd67f",
        "toggle_icon": "☀",
    },
}


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
    # Только "Выучено" сортируется по алфавиту — остальные категории
    # показываются в порядке добавления, так виднее, что добавлено недавно.
    order_clause = "de" if category == LEARNED_CATEGORY else "id"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"SELECT id, de, ru FROM words WHERE category = ? ORDER BY {order_clause}", (category,))
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

    last_error = None
    for attempt in range(TRANSLATE_RETRIES):
        try:
            result = GoogleTranslator(source="de", target="ru").translate(word)
            if result:
                return result
            last_error = RuntimeError("Пустой ответ от переводчика")
        except Exception as e:
            last_error = e
        if attempt < TRANSLATE_RETRIES - 1:
            time.sleep(TRANSLATE_RETRY_DELAY)
    raise last_error


# ---------- Интерфейс ----------

class WortschatzApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = "ru"
        self.language_listeners = []  # функции, вызываемые при смене языка
        self.theme_listeners = []  # функции, вызываемые при смене темы
        self.theme_name = "light"
        self.is_fullscreen = False

        self.geometry("620x560")
        self.minsize(480, 420)
        self.resizable(True, True)

        # Переключатель языка интерфейса — в самом верху окна, виден всегда,
        # на любой вкладке. Меняет только подписи, не сами слова в словаре.
        top_bar = ttk.Frame(self)
        top_bar.pack(fill="x", padx=8, pady=(8, 0))
        self.lang_label = ttk.Label(top_bar, font=("Segoe UI", 9))
        self.lang_label.pack(side="left", padx=(0, 6))
        self.lang_var = tk.StringVar(value=LANG_NAMES[self.lang])
        lang_dropdown = ttk.Combobox(top_bar, textvariable=self.lang_var,
                                      values=list(LANG_NAMES.values()), width=10, state="readonly")
        lang_dropdown.pack(side="left")
        lang_dropdown.bind("<<ComboboxSelected>>", self.handle_language_change)

        # Переключатель светлой/тёмной темы — простая кнопка справа от языка.
        self.theme_button = ttk.Button(top_bar, command=self.toggle_theme, width=3)
        self.theme_button.pack(side="left", padx=(10, 0))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.add_tab = AddWordTab(self.notebook, app=self, on_word_added=self.on_word_added)
        self.dict_tab = DictionaryTab(self.notebook, app=self)
        self.flash_tab = FlashcardsTab(self.notebook, app=self)

        self.notebook.add(self.add_tab, text="")
        self.notebook.add(self.dict_tab, text="")
        self.notebook.add(self.flash_tab, text="")

        self.dict_has_unseen = False

        self.notebook.bind("<<NotebookTabChanged>>", self.handle_tab_changed)
        self.bind("<F11>", self.toggle_fullscreen)

        self.language_listeners.append(self.refresh_tab_titles)
        self.language_listeners.append(self.refresh_lang_bar)
        self.apply_language("ru")
        self.apply_theme("light")

    # ---- Полноэкранный режим ----
    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    # ---- Тема оформления ----
    def toggle_theme(self):
        new_theme = "dark" if self.theme_name == "light" else "light"
        self.apply_theme(new_theme)

    def apply_theme(self, theme_name):
        self.theme_name = theme_name
        palette = THEMES[theme_name]

        style = ttk.Style(self)
        style.theme_use("clam")

        self.configure(bg=palette["bg"])

        style.configure(".", background=palette["bg"], foreground=palette["fg"],
                         fieldbackground=palette["field_bg"])
        style.configure("TFrame", background=palette["bg"])
        style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
        style.configure("TButton", background=palette["field_bg"], foreground=palette["fg"])
        style.map("TButton", background=[("active", palette["select_bg"])])
        style.configure("TEntry", fieldbackground=palette["field_bg"], foreground=palette["fg"])
        style.configure("TCombobox", fieldbackground=palette["field_bg"], foreground=palette["fg"],
                         background=palette["field_bg"])
        style.map("TCombobox", fieldbackground=[("readonly", palette["field_bg"])],
                  foreground=[("readonly", palette["fg"])])
        style.configure("TNotebook", background=palette["bg"])
        style.configure("TNotebook.Tab", background=palette["heading_bg"], foreground=palette["fg"])
        style.map("TNotebook.Tab", background=[("selected", palette["select_bg"])],
                  foreground=[("selected", palette["select_fg"])])
        style.configure("Treeview", background=palette["tree_bg"], foreground=palette["tree_fg"],
                         fieldbackground=palette["tree_bg"])
        style.map("Treeview", background=[("selected", palette["select_bg"])],
                  foreground=[("selected", palette["select_fg"])])
        style.configure("Treeview.Heading", background=palette["heading_bg"], foreground=palette["fg"])

        self.theme_button.config(text=palette["toggle_icon"])

        for listener in self.theme_listeners:
            listener()

    # ---- Язык интерфейса ----
    def t(self, key):
        return TEXTS[self.lang][key]

    def apply_language(self, lang_code):
        self.lang = lang_code
        self.title(self.t("window_title"))
        for listener in self.language_listeners:
            listener()

    def refresh_lang_bar(self):
        self.lang_label.config(text=self.t("lang_label"))
        self.lang_var.set(LANG_NAMES[self.lang])

    def handle_language_change(self, event):
        chosen_name = self.lang_var.get()
        lang_code = LANG_CODES_BY_NAME.get(chosen_name, "ru")
        self.apply_language(lang_code)

    def refresh_tab_titles(self):
        add_title = self.t("tab_add")
        dict_title = self.t("tab_dictionary")
        if self.dict_has_unseen:
            dict_title += " 🔴"
        self.notebook.tab(self.add_tab, text=add_title)
        self.notebook.tab(self.dict_tab, text=dict_title)
        self.notebook.tab(self.flash_tab, text=self.t("tab_flashcards"))

    # ---- Уведомление о новом слове ----
    def on_word_added(self):
        self.dict_tab.refresh_all()
        self.flash_tab.refresh_pool()
        current = self.notebook.select()
        if current != str(self.dict_tab):
            self.dict_has_unseen = True
            self.refresh_tab_titles()

    def handle_tab_changed(self, event):
        if self.notebook.select() == str(self.dict_tab) and self.dict_has_unseen:
            self.dict_has_unseen = False
            self.refresh_tab_titles()


class AddWordTab(ttk.Frame):
    def __init__(self, parent, app, on_word_added):
        super().__init__(parent)
        self.app = app
        self.on_word_added = on_word_added

        self.prompt_label = ttk.Label(self, font=("Segoe UI", 11))
        self.prompt_label.pack(pady=(30, 8))

        self.entry = ttk.Entry(self, width=30, font=("Segoe UI", 12))
        self.entry.pack(pady=4)
        self.entry.bind("<Return>", lambda event: self.handle_add())
        self.entry.focus()

        self.add_button = ttk.Button(self, command=self.handle_add)
        self.add_button.pack(pady=10)

        self.result_label = ttk.Label(self, text="", font=("Segoe UI", 11, "italic"))
        self.result_label.pack(pady=10)

        self.app.language_listeners.append(self.refresh_texts)
        self.refresh_texts()

    def refresh_texts(self):
        self.prompt_label.config(text=self.app.t("add_prompt"))
        self.add_button.config(text=self.app.t("add_button"))

    def handle_add(self):
        word = self.entry.get().strip()
        if not word:
            return

        t = self.app.t
        if word_exists(word):
            messagebox.showinfo(t("already_exists_title"), t("already_exists_msg").format(word=word))
            return

        try:
            translation = translate_de_to_ru(word)
        except Exception as e:
            messagebox.showerror(t("translate_error_title"), str(e))
            return

        # Делаем первую букву заглавной и у слова, и у перевода — даже если
        # ввёл всё строчными буквами.
        word = word[0].upper() + word[1:] if word else word
        translation = translation[0].upper() + translation[1:] if translation else translation

        add_word(word, translation, category="Новые")
        cat_label = t("categories")["Новые"]
        self.result_label.config(text=f"{word} → {translation}  {t('added_suffix').format(cat=cat_label)}")
        self.entry.delete(0, tk.END)
        self.entry.focus()
        self.on_word_added()


class DictionaryTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.category_tabs = {}
        self.inner_notebook = ttk.Notebook(self)
        self.inner_notebook.pack(fill="both", expand=True, padx=4, pady=4)

        for category in CATEGORIES:
            frame = CategoryFrame(self.inner_notebook, category, self, app)
            self.inner_notebook.add(frame, text=category)
            self.category_tabs[category] = frame

        self.app.language_listeners.append(self.refresh_texts)
        self.refresh_texts()

    def refresh_texts(self):
        t = self.app.t
        for category, frame in self.category_tabs.items():
            self.inner_notebook.tab(frame, text=t("categories")[category])

    def refresh_all(self):
        for frame in self.category_tabs.values():
            frame.refresh()


class CategoryFrame(ttk.Frame):
    def __init__(self, parent, category, dictionary_tab, app):
        super().__init__(parent)
        self.category = category
        self.dictionary_tab = dictionary_tab
        self.app = app

        columns = ("de", "ru")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.tree.column("de", width=200)
        self.tree.column("ru", width=200)

        button_row = ttk.Frame(self)
        button_row.pack(fill="x", padx=6, pady=(0, 6))

        self.delete_button = ttk.Button(button_row, command=self.handle_delete)
        self.delete_button.pack(side="left", padx=4)

        self.move_target = tk.StringVar()
        other_categories = [c for c in CATEGORIES if c != self.category]
        self.move_target.set(other_categories[0])
        self.other_categories = other_categories
        self.move_dropdown = ttk.Combobox(button_row, textvariable=self.move_target,
                                           values=other_categories, width=12, state="readonly")
        self.move_dropdown.pack(side="left", padx=4)

        self.move_button = ttk.Button(button_row, command=self.handle_move)
        self.move_button.pack(side="left", padx=4)

        self.app.language_listeners.append(self.refresh_texts)
        self.refresh_texts()
        self.refresh()

    def refresh_texts(self):
        t = self.app.t
        self.tree.heading("de", text=t("col_de"))
        self.tree.heading("ru", text=t("col_ru"))
        self.delete_button.config(text=t("delete_button"))
        self.move_button.config(text=t("move_button"))
        # Выпадающий список "переместить в" показываем переведёнными названиями,
        # но при выборе всё равно сохраняем канонический (русский) ключ категории.
        labels = [t("categories")[c] for c in self.other_categories]
        self.move_dropdown.config(values=labels)
        if self.move_target.get() not in labels:
            self.move_target.set(labels[0])

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        words = get_words(self.category)

        if self.category == LEARNED_CATEGORY:
            # В "Выучено" слова отсортированы по алфавиту — вставляем
            # буквенные разделители между группами, чтобы легче ориентироваться.
            self.tree.tag_configure("header", background="#5c6bc0", foreground="#ffffff")
            current_letter = None
            for header_index, (word_id, de, ru) in enumerate(words):
                letter = de[0].upper() if de else "#"
                if letter != current_letter:
                    current_letter = letter
                    header_iid = f"header_{header_index}_{letter}"
                    self.tree.insert("", tk.END, iid=header_iid, values=(letter, ""), tags=("header",))
                self.tree.insert("", tk.END, iid=str(word_id), values=(de, ru))
        else:
            for word_id, de, ru in words:
                self.tree.insert("", tk.END, iid=str(word_id), values=(de, ru))

    def get_selected_id(self):
        t = self.app.t
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(t("select_word_title"), t("select_word_msg"))
            return None
        try:
            return int(selection[0])
        except ValueError:
            # Выбрана буквенная разделительная строка, а не слово.
            messagebox.showinfo(t("select_word_title"), t("select_word_msg"))
            return None

    def handle_delete(self):
        word_id = self.get_selected_id()
        if word_id is None:
            return
        delete_word(word_id)
        self.refresh()
        self.app.flash_tab.refresh_pool()

    def handle_move(self):
        word_id = self.get_selected_id()
        if word_id is None:
            return
        t = self.app.t
        chosen_label = self.move_target.get()
        # Переводим выбранную подпись обратно в канонический ключ категории
        target_category = self.category
        for canonical, label in t("categories").items():
            if label == chosen_label:
                target_category = canonical
                break
        move_word(word_id, target_category)
        self.refresh()
        self.dictionary_tab.refresh_all()
        self.app.flash_tab.refresh_pool()


class FlashcardsTab(ttk.Frame):
    """Тренировка слов из категории 'Учу': показываем немецкое слово,
    пользователь вспоминает перевод, затем открывает ответ и идёт дальше."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.pool = []
        self.index = 0
        self.showing_answer = False

        self.progress_label = ttk.Label(self, font=("Segoe UI", 9))
        self.progress_label.pack(pady=(20, 0))

        self.intro_label = ttk.Label(self, font=("Segoe UI", 10))
        self.intro_label.pack(pady=(10, 4))

        self.word_label = ttk.Label(self, text="", font=("Segoe UI", 22, "bold"))
        self.word_label.pack(pady=(20, 10))

        self.answer_label = tk.Label(self, text="", font=("Segoe UI", 16))
        self.answer_label.pack(pady=(0, 20))

        button_row = ttk.Frame(self)
        button_row.pack(pady=10)

        self.show_button = ttk.Button(button_row, command=self.handle_show_answer)
        self.show_button.pack(side="left", padx=6)

        self.next_button = ttk.Button(button_row, command=self.handle_next)
        self.next_button.pack(side="left", padx=6)

        self.empty_label = ttk.Label(self, text="", font=("Segoe UI", 11), wraplength=400, justify="center")
        self.empty_label.pack(pady=20)

        self.app.language_listeners.append(self.refresh_texts)
        self.app.theme_listeners.append(self.refresh_theme)
        self.refresh_texts()
        self.refresh_theme()
        self.refresh_pool()

    def refresh_theme(self):
        palette = THEMES[self.app.theme_name]
        self.answer_label.config(fg=palette["answer_color"], bg=palette["bg"])

    def refresh_texts(self):
        t = self.app.t
        self.intro_label.config(text=t("flash_intro"))
        self.show_button.config(text=t("flash_show_answer"))
        self.next_button.config(text=t("flash_next"))
        self.empty_label.config(text=t("flash_empty"))
        self.update_progress_label()

    def refresh_pool(self):
        self.pool = get_words(LEARNING_CATEGORY)
        random.shuffle(self.pool)
        self.index = 0
        self.showing_answer = False
        self.show_current()

    def update_progress_label(self):
        if self.pool:
            text = self.app.t("flash_progress").format(current=self.index + 1, total=len(self.pool))
        else:
            text = ""
        self.progress_label.config(text=text)

    def show_current(self):
        self.update_progress_label()
        has_words = bool(self.pool)
        self.word_label.pack_forget()
        self.answer_label.pack_forget()
        self.intro_label.pack_forget()
        self.empty_label.pack_forget()

        if not has_words:
            self.empty_label.pack(pady=20)
            self.answer_label.config(text="")
            return

        self.intro_label.pack(pady=(10, 4))
        self.word_label.pack(pady=(20, 10))
        self.answer_label.pack(pady=(0, 20))

        word_id, de, ru = self.pool[self.index]
        self.word_label.config(text=de)
        self.answer_label.config(text=ru if self.showing_answer else "")

    def handle_show_answer(self):
        if not self.pool:
            return
        self.showing_answer = True
        self.show_current()

    def handle_next(self):
        if not self.pool:
            return
        self.index = (self.index + 1) % len(self.pool)
        self.showing_answer = False
        self.show_current()


if __name__ == "__main__":
    init_db()
    app = WortschatzApp()
    app.mainloop()