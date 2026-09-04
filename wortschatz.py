"""
Wortschatz is an app for learning German words.
German -> Russian, automatic translation via Google Translate,
word storage in a local SQLite database, categories: New / Learning / Learned.

Run: python wortschatz.py
Before the first run, install the translation library once:
pip install deep-translator
"""
"""
Wortschatz — An app for learning German words.
The design is inspired by the author's personal portfolio website: a black navigation bar,
a light gray canvas, large cards with a bold border and a large rounding,
a black/white inversion between the card and the buttons on it.
"""

import sqlite3
import time
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import random

import customtkinter as ctk

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(APP_DIR, "wortschatz.db")

CATEGORIES = ["Новые", "Учу", "Выучено"]
LEARNING_CATEGORY = "Учу"
LEARNED_CATEGORY = "Выучено"

TRANSLATE_RETRIES = 3
TRANSLATE_RETRY_DELAY = 0.6

# ---------- Дизайн-система: чёрная рамка, большой радиус, инверсия цветов ----------

PALETTE = {
    "light": {
        "canvas": "#f2f2f2",
        "navbar": "#111113",
        "navbar_text": "#ffffff",
        "navbar_text_dim": "#a1a1aa",
        "card_dark_bg": "#111113",
        "card_dark_text": "#ffffff",
        "card_light_bg": "#ffffff",
        "card_light_text": "#111113",
        # Цвет для элементов, которым нужен контраст ИМЕННО с тёмной карточкой
        # (card_dark_bg) — в светлой теме это просто белый, в тёмной — не
        # совпадает ни с одним из фонов карточек, иначе кнопка "исчезает".
        "invert_bg": "#ffffff",
        "invert_text": "#111113",
        "border": "#111113",
        "subtext": "#6b7280",
        "success": "#16a34a",
        "entry_bg": "#f5f5f5",
        "navbar_hover": "#27272a",
        # Приглушённый текст ИМЕННО на тёмной карточке. Отдельно от
        # navbar_text_dim: тот рассчитан на навбар и в тёмной теме даёт на
        # карточке всего 3.6:1 — ниже нормы читаемости.
        "card_dim_text": "#a1a1aa",
        "card_track": "#5a5a61",
        "theme_icon": "🌙",
    },
    "dark": {
        "canvas": "#0d0d0f",
        "navbar": "#000000",
        "navbar_text": "#f5f5f5",
        "navbar_text_dim": "#71717a",
        "card_dark_bg": "#1a1a1d",
        "card_dark_text": "#f5f5f5",
        "card_light_bg": "#151517",
        "card_light_text": "#f5f5f5",
        "invert_bg": "#f5f5f5",
        "invert_text": "#1a1a1d",
        "border": "#f5f5f5",
        "subtext": "#a1a1aa",
        "success": "#4ade80",
        "entry_bg": "#2a2a2e",
        "navbar_hover": "#1c1c1f",
        "card_dim_text": "#a1a1aa",
        "card_track": "#5f5f67",
        "theme_icon": "☀",
    },
}

FONT = "Segoe UI"


def F(size, weight="normal"):
    return (FONT, size, weight)


TEXTS = {
    "ru": {
        "window_title": "Wortschatz",
        "tab_add": "Добавить",
        "tab_dictionary": "Словарь",
        "tab_flashcards": "Карточки",
        "add_heading": "Новое слово",
        "add_prompt": "Немецкое слово",
        "add_button": "Перевести и добавить",
        "added_suffix": "добавлено в «{cat}»",
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
        "flash_empty": "В категории «Учу» пока нет слов для повторения.",
        "flash_progress": "{current} / {total}",
        "flash_side_question": "Вопрос",
        "flash_side_answer": "Ответ",
        "flash_hint_flip": "Нажми на карточку, чтобы перевернуть",
        "flash_know": "Знаю",
        "flash_still": "Ещё учу",
        "flash_restart": "Пройти заново",
        "flash_done_title": "Раунд пройден",
        "flash_done_sub": "Знаю: {known}   ·   Ещё учу: {still}",
        "flash_keys_hint": "Пробел — перевернуть   ·   ← →  листать",
    },
    "en": {
        "window_title": "Wortschatz",
        "tab_add": "Add",
        "tab_dictionary": "Dictionary",
        "tab_flashcards": "Flashcards",
        "add_heading": "New word",
        "add_prompt": "German word",
        "add_button": "Translate & add",
        "added_suffix": "added to “{cat}”",
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
        "flash_empty": "No words under “Learning” yet.",
        "flash_progress": "{current} / {total}",
        "flash_side_question": "Question",
        "flash_side_answer": "Answer",
        "flash_hint_flip": "Click the card to flip it",
        "flash_know": "I know it",
        "flash_still": "Still learning",
        "flash_restart": "Start over",
        "flash_done_title": "Round complete",
        "flash_done_sub": "Knew it: {known}   ·   Still learning: {still}",
        "flash_keys_hint": "Space — flip   ·   ← →  navigate",
    },
    "de": {
        "window_title": "Wortschatz",
        "tab_add": "Hinzufügen",
        "tab_dictionary": "Wörterbuch",
        "tab_flashcards": "Karteikarten",
        "add_heading": "Neues Wort",
        "add_prompt": "Deutsches Wort",
        "add_button": "Übersetzen & hinzufügen",
        "already_exists_title": "Bereits vorhanden",
        "already_exists_msg": 'Das Wort "{word}" ist bereits im Wörterbuch.',
        "added_suffix": "zu „{cat}“ hinzugefügt",
        "translate_error_title": "Übersetzungsfehler",
        "delete_button": "Löschen",
        "move_button": "Verschieben",
        "select_word_title": "Wort auswählen",
        "select_word_msg": "Bitte zuerst ein Wort in der Liste auswählen.",
        "col_de": "Deutsch",
        "col_ru": "Russisch",
        "categories": {"Новые": "Neu", "Учу": "Lernen", "Выучено": "Gelernt"},
        "flash_empty": "Noch keine Wörter unter „Lernen“.",
        "flash_progress": "{current} / {total}",
        "flash_side_question": "Frage",
        "flash_side_answer": "Antwort",
        "flash_hint_flip": "Zum Umdrehen auf die Karte klicken",
        "flash_know": "Kann ich",
        "flash_still": "Lerne ich noch",
        "flash_restart": "Neue Runde",
        "flash_done_title": "Runde geschafft",
        "flash_done_sub": "Kann ich: {known}   ·   Lerne ich noch: {still}",
        "flash_keys_hint": "Leertaste — umdrehen   ·   ← →  blättern",
    },
}

LANG_NAMES = {"ru": "Русский", "en": "English", "de": "Deutsch"}
LANG_CODES_BY_NAME = {v: k for k, v in LANG_NAMES.items()}


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


# ---------- Анимация: крошечный движок твинов на after() ----------
#
# Всё движение считается по РЕАЛЬНОМУ времени, а не по числу отрисованных
# кадров: если система подтормозит, анимация не растянется — она просто
# пропустит промежуточные кадры и придёт в конечное состояние вовремя.

ANIM_FRAME_MS = 16        # ~60 кадров в секунду
FLIP_MS = 280             # полный переворот карточки (две половины по 140)
SLIDE_OUT_MS = 170        # карточка уезжает за край
SLIDE_IN_MS = 240         # и следующая приезжает с другой стороны
PROGRESS_MS = 340         # полоса прогресса догоняет новое значение
HOVER_MS = 130            # подсветка карточки под курсором
HOVER_LIFT = 0.10         # насколько фон карточки светлеет при наведении
BUTTON_HOVER_MIX = 0.16   # насколько кнопка на карточке сдвигается к цвету своего текста


def ease_in_cubic(t):
    """Разгон: медленно в начале — годится для «ухода» элемента."""
    return t * t * t


def ease_out_cubic(t):
    """Торможение: быстро в начале — годится для «прихода» элемента."""
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def mix_colors(color_a, color_b, t):
    """Смешивает два HEX-цвета: t=0 — первый, t=1 — второй."""
    a = color_a.lstrip("#")
    b = color_b.lstrip("#")
    channels = []
    for i in (0, 2, 4):
        channels.append(int(round(lerp(int(a[i:i + 2], 16), int(b[i:i + 2], 16), t))))
    return "#{:02x}{:02x}{:02x}".format(*channels)


class Animator:
    """Набор именованных твинов одного виджета.

    Запуск твина с уже занятым именем отменяет предыдущий — поэтому быстрые
    повторные клики не накладывают анимации друг на друга. Все таймеры лежат
    в одном словаре и гасятся разом (cancel без имени) при смене темы, языка,
    перезагрузке пула и уничтожении вкладки — так после себя не остаётся
    ни одного «висящего» after.
    """

    def __init__(self, widget):
        self._widget = widget
        self._jobs = {}

    def run(self, name, duration_ms, on_frame, on_done=None, easing=ease_out_cubic):
        self.cancel(name)
        started = time.perf_counter()

        def step():
            # Имя снимаем сразу: иначе твин, запущенный из on_done под тем же
            # именем, был бы тут же отменён этой же записью.
            self._jobs.pop(name, None)
            if not self._widget.winfo_exists():
                return
            elapsed_ms = (time.perf_counter() - started) * 1000
            raw = 1.0 if duration_ms <= 0 else min(1.0, elapsed_ms / duration_ms)
            on_frame(easing(raw))
            if raw >= 1.0:
                if on_done is not None:
                    on_done()
            else:
                self._jobs[name] = self._widget.after(ANIM_FRAME_MS, step)

        step()  # первый кадр рисуем сразу, без задержки в 16 мс

    def cancel(self, name=None):
        for key in ([name] if name is not None else list(self._jobs)):
            job = self._jobs.pop(key, None)
            if job is None:
                continue
            try:
                self._widget.after_cancel(job)
            except Exception:
                pass  # виджет мог быть уже уничтожен вместе со своими таймерами

    def is_running(self, name=None):
        return name in self._jobs if name is not None else bool(self._jobs)


# ---------- Интерфейс ----------

ctk.set_default_color_theme("blue")


class WortschatzApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.lang = "ru"
        self.language_listeners = []
        self.theme_listeners = []
        self.theme_name = "light"
        self.is_fullscreen = False
        self.dict_has_unseen = False

        self.geometry("820x660")
        self.minsize(640, 520)

        # ---- Навигационная панель — на всю ширину, тёмная, как на сайте ----
        self.navbar = ctk.CTkFrame(self, corner_radius=0, height=64)
        self.navbar.pack(fill="x", side="top")
        self.navbar.pack_propagate(False)

        self.title_label = ctk.CTkLabel(self.navbar, text="Wortschatz", font=F(18, "bold"))
        self.title_label.pack(side="left", padx=(24, 40))

        self.nav_buttons = {}
        nav_row = ctk.CTkFrame(self.navbar, fg_color="transparent")
        nav_row.pack(side="left", fill="y")
        for key in ("add", "dict", "flash"):
            btn = ctk.CTkButton(nav_row, text="", fg_color="transparent", corner_radius=6,
                                 font=F(13, "bold"), width=110, height=36,
                                 hover_color=PALETTE["light"]["navbar_hover"],
                                 command=lambda k=key: self.show_page(k))
            btn.pack(side="left", padx=4)
            self.nav_buttons[key] = btn

        right_controls = ctk.CTkFrame(self.navbar, fg_color="transparent")
        right_controls.pack(side="right", padx=24)

        self.lang_var = ctk.StringVar(value=LANG_NAMES[self.lang])
        self.lang_menu = ctk.CTkOptionMenu(right_controls, variable=self.lang_var,
                                            values=list(LANG_NAMES.values()),
                                            command=self.handle_language_change,
                                            width=100, height=32, corner_radius=6, font=F(11))
        self.lang_menu.pack(side="left", padx=(0, 8))

        self.theme_button = ctk.CTkButton(right_controls, text="🌙", width=32, height=32,
                                           corner_radius=6, command=self.toggle_theme, font=F(13))
        self.theme_button.pack(side="left")

        # ---- Содержимое страниц ----
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True, padx=28, pady=28)

        self.add_tab = AddWordTab(self.content_area, app=self, on_word_added=self.on_word_added)
        self.dict_tab = DictionaryTab(self.content_area, app=self)
        self.flash_tab = FlashcardsTab(self.content_area, app=self)

        self.pages = {"add": self.add_tab, "dict": self.dict_tab, "flash": self.flash_tab}
        self.current_page = "add"

        self.bind("<F11>", self.toggle_fullscreen)

        self.language_listeners.append(self.refresh_nav_texts)
        self.apply_language("ru")
        self.apply_theme("light")
        self.show_page("add")

    # ---- Навигация между страницами ----
    def show_page(self, key):
        for name, page in self.pages.items():
            if name == key:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()
        self.current_page = key
        if key == "dict" and self.dict_has_unseen:
            self.dict_has_unseen = False
            self.refresh_nav_texts()
        self.refresh_nav_active_state()

    def refresh_nav_active_state(self):
        p = PALETTE[self.theme_name]
        for key, btn in self.nav_buttons.items():
            btn.configure(hover_color=p["navbar_hover"])
            if key == self.current_page:
                btn.configure(text_color=p["navbar_text"])
            else:
                btn.configure(text_color=p["navbar_text_dim"])

    # ---- Полноэкранный режим ----
    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    # ---- Тема ----
    def toggle_theme(self):
        new_theme = "dark" if self.theme_name == "light" else "light"
        self.apply_theme(new_theme)

    def apply_theme(self, theme_name):
        self.theme_name = theme_name
        p = PALETTE[theme_name]

        ctk.set_appearance_mode("dark" if theme_name == "dark" else "light")
        self.configure(fg_color=p["canvas"])

        self.navbar.configure(fg_color=p["navbar"])
        self.title_label.configure(text_color=p["navbar_text"])
        self.theme_button.configure(text=p["theme_icon"], fg_color=p["navbar_text_dim"],
                                     text_color=p["navbar"], hover_color=p["navbar_text"])
        self.lang_menu.configure(fg_color=p["navbar_text_dim"], text_color=p["navbar"],
                                  button_color=p["navbar_text"], button_hover_color=p["navbar_text_dim"],
                                  dropdown_fg_color=p["card_light_bg"], dropdown_text_color=p["card_light_text"])

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=p["card_light_bg"], foreground=p["card_light_text"],
                         fieldbackground=p["card_light_bg"], rowheight=32, borderwidth=0, font=F(11))
        # Подсветка выделения (border) в тёмной теме светлая, а в светлой — тёмная,
        # поэтому текст выделенной строки берём из card_light_bg: он всегда
        # противоположен border по яркости (тёмный в dark-теме, белый в light-теме).
        style.map("Treeview", background=[("selected", p["border"])],
                  foreground=[("selected", p["card_light_bg"])])
        style.configure("Treeview.Heading", background=p["entry_bg"], foreground=p["subtext"],
                         font=F(10, "bold"), borderwidth=0, relief="flat")
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

        self.refresh_nav_active_state()
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

    def handle_language_change(self, chosen_name):
        lang_code = LANG_CODES_BY_NAME.get(chosen_name, "ru")
        self.apply_language(lang_code)

    def refresh_nav_texts(self):
        dict_title = self.t("tab_dictionary")
        if self.dict_has_unseen:
            dict_title += "  •"
        self.nav_buttons["add"].configure(text=self.t("tab_add"))
        self.nav_buttons["dict"].configure(text=dict_title)
        self.nav_buttons["flash"].configure(text=self.t("tab_flashcards"))

    # ---- Уведомление о новом слове ----
    def on_word_added(self):
        self.dict_tab.refresh_all()
        self.flash_tab.refresh_pool()
        if self.current_page != "dict":
            self.dict_has_unseen = True
            self.refresh_nav_texts()


class AddWordTab(ctk.CTkFrame):
    """Тёмная карточка на светлом холсте — как блок 'Grüessli' на сайте."""

    def __init__(self, parent, app, on_word_added):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.on_word_added = on_word_added

        self.card = ctk.CTkFrame(self, corner_radius=20, border_width=2)
        self.card.pack(expand=True, fill="both")

        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        self.heading_label = ctk.CTkLabel(inner, font=F(24, "bold"))
        self.heading_label.pack(pady=(0, 4))

        self.prompt_label = ctk.CTkLabel(inner, font=F(11, "bold"))
        self.prompt_label.pack(anchor="w", pady=(20, 6))

        self.entry = ctk.CTkEntry(inner, width=360, height=44, font=F(14), corner_radius=10,
                                   border_width=2)
        self.entry.pack(pady=(0, 20))
        self.entry.bind("<Return>", lambda event: self.handle_add())

        self.add_button = ctk.CTkButton(inner, command=self.handle_add, height=44, width=360,
                                         corner_radius=10, font=F(13, "bold"))
        self.add_button.pack()

        self.result_label = ctk.CTkLabel(inner, text="", font=F(12), wraplength=360)
        self.result_label.pack(pady=(18, 0))

        self.app.language_listeners.append(self.refresh_texts)
        self.app.theme_listeners.append(self.refresh_theme)
        self.refresh_texts()
        self.refresh_theme()

    def refresh_theme(self):
        p = PALETTE[self.app.theme_name]
        self.card.configure(fg_color=p["card_dark_bg"], border_color=p["border"])
        self.heading_label.configure(text_color=p["card_dark_text"])
        self.prompt_label.configure(text_color=p["navbar_text_dim"])
        self.entry.configure(fg_color=p["invert_bg"], text_color=p["invert_text"],
                              border_color=p["card_dark_text"])
        # Кнопка — инверсия относительно тёмной карточки: светлый фон, тёмный текст.
        self.add_button.configure(fg_color=p["invert_bg"], hover_color=p["entry_bg"],
                                   text_color=p["invert_text"])
        self.result_label.configure(text_color=p["success"])

    def refresh_texts(self):
        self.heading_label.configure(text=self.app.t("add_heading"))
        self.prompt_label.configure(text=self.app.t("add_prompt").upper())
        self.add_button.configure(text=self.app.t("add_button"))

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

        word = word[0].upper() + word[1:] if word else word
        translation = translation[0].upper() + translation[1:] if translation else translation

        add_word(word, translation, category="Новые")
        cat_label = t("categories")["Новые"]
        self.result_label.configure(text=f"{word} → {translation}   ·   {t('added_suffix').format(cat=cat_label)}")
        self.entry.delete(0, "end")
        self.entry.focus()
        self.on_word_added()


class DictionaryTab(ctk.CTkFrame):
    """Светлая карточка с чёрной рамкой — как блок 'Skills' на сайте."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.card = ctk.CTkFrame(self, corner_radius=20, border_width=2)
        self.card.pack(expand=True, fill="both")

        sub_nav = ctk.CTkFrame(self.card, fg_color="transparent")
        sub_nav.pack(fill="x", padx=24, pady=(24, 12))

        self.sub_buttons = {}
        for category in CATEGORIES:
            btn = ctk.CTkButton(sub_nav, text="", corner_radius=8, height=34,
                                 font=F(12, "bold"), command=lambda c=category: self.show_category(c))
            btn.pack(side="left", padx=(0, 8))
            self.sub_buttons[category] = btn

        self.category_tabs = {}
        self.body = ctk.CTkFrame(self.card, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        for category in CATEGORIES:
            frame = CategoryFrame(self.body, category, self, app)
            self.category_tabs[category] = frame

        self.current_category = CATEGORIES[0]

        self.app.language_listeners.append(self.refresh_texts)
        self.app.theme_listeners.append(self.refresh_theme)
        self.refresh_texts()
        self.refresh_theme()
        self.show_category(CATEGORIES[0])

    def show_category(self, category):
        for name, frame in self.category_tabs.items():
            if name == category:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        self.current_category = category
        self.refresh_sub_nav_state()

    def refresh_sub_nav_state(self):
        p = PALETTE[self.app.theme_name]
        for category, btn in self.sub_buttons.items():
            if category == self.current_category:
                btn.configure(fg_color=p["card_dark_bg"], text_color=p["card_dark_text"],
                               hover_color=p["card_dark_bg"])
            else:
                btn.configure(fg_color="transparent", text_color=p["subtext"], hover_color=p["entry_bg"])

    def refresh_theme(self):
        p = PALETTE[self.app.theme_name]
        self.card.configure(fg_color=p["card_light_bg"], border_color=p["border"])
        self.refresh_sub_nav_state()

    def refresh_texts(self):
        t = self.app.t
        for category, btn in self.sub_buttons.items():
            btn.configure(text=t("categories")[category])

    def refresh_all(self):
        for frame in self.category_tabs.values():
            frame.refresh()


class CategoryFrame(ctk.CTkFrame):
    def __init__(self, parent, category, dictionary_tab, app):
        super().__init__(parent, fg_color="transparent")
        self.category = category
        self.dictionary_tab = dictionary_tab
        self.app = app

        columns = ("de", "ru")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        self.tree.pack(fill="both", expand=True, pady=(0, 12))
        self.tree.column("de", width=240)
        self.tree.column("ru", width=240)

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(fill="x")

        self.delete_button = ctk.CTkButton(button_row, command=self.handle_delete,
                                            width=110, height=36, corner_radius=8, font=F(12, "bold"))
        self.delete_button.pack(side="left", padx=(0, 8))

        self.move_target = ctk.StringVar()
        self.other_categories = [c for c in CATEGORIES if c != self.category]
        self.move_target.set(self.other_categories[0])
        self.move_dropdown = ctk.CTkOptionMenu(button_row, variable=self.move_target,
                                                values=self.other_categories, width=130,
                                                height=36, corner_radius=8, font=F(12))
        self.move_dropdown.pack(side="left", padx=(0, 8))

        self.move_button = ctk.CTkButton(button_row, command=self.handle_move,
                                          width=110, height=36, corner_radius=8, font=F(12, "bold"))
        self.move_button.pack(side="left")

        self.app.language_listeners.append(self.refresh_texts)
        self.app.theme_listeners.append(self.refresh_theme)
        self.refresh_texts()
        self.refresh_theme()
        self.refresh()

    def refresh_theme(self):
        p = PALETTE[self.app.theme_name]
        self.tree.tag_configure("header", background=p["navbar"], foreground=p["navbar_text"])
        # Кнопки — жирные чёрные пилюли с белым текстом, как ссылки на сайте.
        self.delete_button.configure(fg_color="transparent", border_width=2, border_color=p["border"],
                                      text_color=p["card_light_text"], hover_color=p["entry_bg"])
        self.move_button.configure(fg_color=p["card_dark_bg"], hover_color=p["navbar_text_dim"],
                                    text_color=p["card_dark_text"])
        self.move_dropdown.configure(fg_color=p["entry_bg"], text_color=p["card_light_text"],
                                      button_color=p["border"], button_hover_color=p["subtext"],
                                      dropdown_fg_color=p["card_light_bg"], dropdown_text_color=p["card_light_text"])

    def refresh_texts(self):
        t = self.app.t
        self.tree.heading("de", text=t("col_de").upper())
        self.tree.heading("ru", text=t("col_ru").upper())
        self.delete_button.configure(text=t("delete_button"))
        self.move_button.configure(text=t("move_button"))
        labels = [t("categories")[c] for c in self.other_categories]
        self.move_dropdown.configure(values=labels)
        if self.move_target.get() not in labels:
            self.move_target.set(labels[0])

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        words = get_words(self.category)

        if self.category == LEARNED_CATEGORY:
            current_letter = None
            for header_index, (word_id, de, ru) in enumerate(words):
                letter = de[0].upper() if de else "#"
                if letter != current_letter:
                    current_letter = letter
                    header_iid = f"header_{header_index}_{letter}"
                    self.tree.insert("", "end", iid=header_iid, values=(letter, ""), tags=("header",))
                self.tree.insert("", "end", iid=str(word_id), values=(de, ru))
        else:
            for word_id, de, ru in words:
                self.tree.insert("", "end", iid=str(word_id), values=(de, ru))

    def get_selected_id(self):
        t = self.app.t
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(t("select_word_title"), t("select_word_msg"))
            return None
        try:
            return int(selection[0])
        except ValueError:
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
        target_category = self.category
        for canonical, label in t("categories").items():
            if label == chosen_label:
                target_category = canonical
                break
        move_word(word_id, target_category)
        self.refresh()
        self.dictionary_tab.refresh_all()
        self.app.flash_tab.refresh_pool()


class FlashcardsTab(ctk.CTkFrame):
    """Карточки в духе Quizlet: переворот, слайд между словами, живой прогресс.

    Раскладка нарочно статична: ни один виджет не переупаковывается при смене
    состояния — меняются только тексты, цвета и то, какой из двух рядов кнопок
    «положен» через place. Так исключена ловушка прежней версии, где повторный
    pack() отправлял виджет в конец очереди упаковки и кнопки уезжали вниз.
    """

    FLIP_MIN_WIDTH = 0.10   # ширина карточки в середине переворота (доля сцены)
    SLIDE_OFFSET = 0.85     # насколько карточка уезжает за край при смене слова
    WORD_SIZE = 32          # обычный кегль слова
    WORD_SIZE_MIN = 12      # на «ребре» слово уходит в перспективу
    EMPTY_SIZE = 14         # текст пустого состояния — обычный, не заголовочный
    SLIDE_FADE = 0.25       # до какой прозрачности гаснет карточка, пока уезжает

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.round = []            # снимок слов на раунд: список (id, de, ru)
        self.index = 0
        self.showing_answer = False
        self.known_count = 0
        self.still_count = 0
        self.finished = False      # раунд пройден, показан итоговый экран
        self.hovered = False

        self.anim = Animator(self)

        self.card = ctk.CTkFrame(self, corner_radius=20, border_width=2)
        self.card.pack(expand=True, fill="both")

        # ---- Верх: счётчик и полоса прогресса ----
        self.top_bar = ctk.CTkFrame(self.card, fg_color="transparent", height=18)
        self.top_bar.pack(fill="x", padx=28, pady=(22, 0))

        self.progress_label = ctk.CTkLabel(self.top_bar, text="", font=F(11, "bold"))
        self.progress_label.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(self.top_bar, height=6, corner_radius=3)
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=(20, 0))
        self.progress_bar.set(0)

        # ---- Сцена: единственное, что двигается ----
        self.stage = ctk.CTkFrame(self.card, fg_color="transparent")
        self.stage.pack(expand=True, fill="both", padx=28)

        # flip_box держим через place: только place позволяет плавно менять
        # ширину (переворот) и смещение (слайд), не трогая соседей по раскладке.
        self.flip_box = ctk.CTkFrame(self.stage, fg_color="transparent")
        self.flip_box.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0)

        self.side_label = ctk.CTkLabel(self.flip_box, text="", font=F(11, "bold"))
        self.side_label.pack()

        # Шрифт слова держим отдельным объектом: CTkFont меняет кегль на лету и
        # сам перерисовывает подписанные виджеты — отсюда честное масштабирование
        # текста при перевороте, а не грубая обрезка по краю контейнера.
        self.word_font = ctk.CTkFont(family=FONT, size=self.WORD_SIZE, weight="bold")
        # Перенос строки с запасом под минимальный размер окна (640x520):
        # сцена там всего ~528 px, при большем wraplength текст обрезался бы.
        self.word_label = ctk.CTkLabel(self.flip_box, text="", font=self.word_font,
                                        wraplength=480, justify="center")
        self.word_label.pack(pady=(14, 0))

        self.hint_label = ctk.CTkLabel(self.flip_box, text="", font=F(11),
                                        wraplength=460, justify="center")
        self.hint_label.pack(pady=(16, 0))

        # ---- Низ: два ряда кнопок в одном гнезде, переключаются через place ----
        self.bottom_bar = ctk.CTkFrame(self.card, fg_color="transparent", height=46)
        self.bottom_bar.pack(fill="x", padx=28)
        self.bottom_bar.pack_propagate(False)

        self.round_row = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        self.still_button = ctk.CTkButton(self.round_row, command=self.handle_still,
                                           corner_radius=10, width=170, height=42, font=F(12, "bold"))
        self.still_button.pack(side="left", padx=6)
        self.know_button = ctk.CTkButton(self.round_row, command=self.handle_know,
                                          corner_radius=10, width=170, height=42, font=F(12, "bold"))
        self.know_button.pack(side="left", padx=6)

        self.done_row = ctk.CTkFrame(self.bottom_bar, fg_color="transparent")
        self.restart_button = ctk.CTkButton(self.done_row, command=self.handle_restart,
                                             corner_radius=10, width=220, height=42, font=F(12, "bold"))
        self.restart_button.pack()

        self.keys_label = ctk.CTkLabel(self.card, text="", font=F(11))
        self.keys_label.pack(pady=(10, 18))

        # ---- Карточка кликабельна целиком ----
        # bind у CTkFrame вешается только на его собственный канвас, поэтому
        # клик и наведение подписываем на каждый виджет сцены отдельно.
        for widget in (self.card, self.stage, self.flip_box, self.top_bar, self.bottom_bar,
                       self.progress_label, self.keys_label,
                       self.side_label, self.word_label, self.hint_label):
            widget.bind("<Button-1>", self._on_card_click)
            widget.bind("<Enter>", self._on_card_enter)
            widget.bind("<Leave>", self._on_card_leave)
            widget.configure(cursor="hand2")

        # ---- Клавиатура: слушаем корень, но реагируем только на своей вкладке ----
        self.app.bind("<space>", self._on_key_flip, add="+")
        self.app.bind("<Right>", self._on_key_next, add="+")
        self.app.bind("<Left>", self._on_key_prev, add="+")

        # Вкладка живёт столько же, сколько приложение, но если её всё-таки
        # уничтожат — гасим все таймеры, чтобы after не стрелял в пустоту.
        self.bind("<Destroy>", self._on_destroy)

        self.app.language_listeners.append(self.refresh_texts)
        self.app.theme_listeners.append(self.refresh_theme)
        self.refresh_texts()
        self.refresh_theme()
        self.refresh_pool()

    # ---- Оформление ----

    def refresh_theme(self):
        p = PALETTE[self.app.theme_name]
        # Смена темы во время анимации: переворот и подсветку гасим и
        # распрямляем карточку, а слайд НЕ трогаем — его отложенный шаг меняет
        # текущее слово, и обрыв посреди пути потерял бы ход пользователя.
        sliding = self.anim.is_running("slide")
        self.anim.cancel("flip")
        self.anim.cancel("hover")
        self.hovered = False
        if not sliding:
            self._reset_stage()

        self.card.configure(fg_color=p["card_dark_bg"], border_color=p["border"])
        self.progress_label.configure(text_color=p["card_dim_text"])
        self.progress_bar.configure(fg_color=p["card_track"], progress_color=p["card_dark_text"])
        self.keys_label.configure(text_color=p["card_dim_text"])
        # Кнопки — инверсия: светлые на тёмной карточке. «Ещё учу» обведена,
        # «Знаю» залита, как основное действие. Цвет наведения считаем от
        # собственного фона кнопки: токен entry_bg в тёмной теме тёмный и
        # съел бы тёмный текст на светлой кнопке.
        self.still_button.configure(fg_color="transparent", border_width=2,
                                     border_color=p["card_dark_text"], text_color=p["card_dark_text"],
                                     hover_color=mix_colors(p["card_dark_bg"], p["card_dark_text"],
                                                            BUTTON_HOVER_MIX))
        invert_hover = mix_colors(p["invert_bg"], p["invert_text"], BUTTON_HOVER_MIX)
        self.know_button.configure(fg_color=p["invert_bg"], hover_color=invert_hover,
                                    text_color=p["invert_text"])
        self.restart_button.configure(fg_color=p["invert_bg"], hover_color=invert_hover,
                                       text_color=p["invert_text"])
        self._render()
        self._render_progress(animate=False)

    def refresh_texts(self):
        t = self.app.t
        self.still_button.configure(text=t("flash_still"))
        self.know_button.configure(text=t("flash_know"))
        self.restart_button.configure(text=t("flash_restart"))
        self._render()   # тексты сцены и подсказку про клавиши ставит он же
        self._render_progress(animate=False)

    # ---- Состояние раунда ----

    def refresh_pool(self):
        """Начинает раунд заново по текущему содержимому категории «Учу»."""
        self.anim.cancel()
        # Твин подсветки оборван на полпути — возвращаем карточке базовый фон,
        # иначе она залипнет на промежуточном оттенке до следующего ухода мыши.
        self.hovered = False
        self.card.configure(fg_color=PALETTE[self.app.theme_name]["card_dark_bg"])
        self._reset_stage()
        self._reload_round()
        self._render()
        self._render_progress(animate=False)

    def _reload_round(self):
        """Забирает свежий снимок слов и сбрасывает счётчики раунда."""
        self.round = get_words(LEARNING_CATEGORY)
        random.shuffle(self.round)
        self.index = 0
        self.showing_answer = False
        self.known_count = 0
        self.still_count = 0
        self.finished = False

    def _reset_stage(self):
        """Возвращает карточку в исходное положение после прерванной анимации."""
        self.flip_box.place_configure(relx=0.5, relwidth=1.0)

    def _render(self):
        """Единственная точка правды: приводит виджеты к текущему состоянию."""
        p = PALETTE[self.app.theme_name]
        t = self.app.t
        dim = p["card_dim_text"]
        total = len(self.round)
        # Подсказка про клавиши уместна только там, где клавиши работают:
        # на итоговом и на пустом экране ни переворота, ни листания нет.
        active = bool(self.round) and not self.finished
        self.keys_label.configure(text=t("flash_keys_hint") if active else "")

        if self.finished:
            self.word_font.configure(size=self.WORD_SIZE, weight="bold")
            self.side_label.configure(text=t("flash_done_title").upper(), text_color=dim)
            self.word_label.configure(text="{} / {}".format(self.known_count, total),
                                       text_color=self._word_color())
            self.hint_label.configure(text=t("flash_done_sub").format(known=self.known_count,
                                                                      still=self.still_count),
                                       text_color=dim)
            self._show_button_row(self.done_row)
            return

        if not self.round:
            # Пустое состояние — обычный текст, а не заголовок: кегль мельче.
            self.word_font.configure(size=self.EMPTY_SIZE, weight="normal")
            self.side_label.configure(text="", text_color=dim)
            self.word_label.configure(text=t("flash_empty"), text_color=self._word_color())
            self.hint_label.configure(text="", text_color=dim)
            self._show_button_row(None)
            return

        word_id, de, ru = self.round[self.index]
        self.word_font.configure(size=self.WORD_SIZE, weight="bold")
        self.word_label.configure(text=ru if self.showing_answer else de,
                                   text_color=self._word_color())
        if self.showing_answer:
            self.side_label.configure(text=t("flash_side_answer").upper(), text_color=dim)
            # На обороте оставляем само слово мелким — видно обе стороны сразу.
            self.hint_label.configure(text=de, text_color=dim)
        else:
            self.side_label.configure(text=t("flash_side_question").upper(), text_color=dim)
            self.hint_label.configure(text=t("flash_hint_flip"), text_color=dim)
        self._show_button_row(self.round_row)

    def _show_button_row(self, row):
        """Кладёт нужный ряд кнопок в общее гнездо; place не зависит от порядка."""
        for candidate in (self.round_row, self.done_row):
            if candidate is row:
                candidate.place(relx=0.5, rely=0.5, anchor="center")
            else:
                candidate.place_forget()

    def _render_progress(self, animate=True):
        t = self.app.t
        total = len(self.round)
        if not total:
            self.progress_label.configure(text="")
            target = 0.0
        elif self.finished:
            self.progress_label.configure(text=t("flash_progress").format(current=total, total=total))
            target = 1.0
        else:
            self.progress_label.configure(text=t("flash_progress").format(current=self.index + 1, total=total))
            target = (self.index + 1) / total

        if animate:
            start = self.progress_bar.get()
            self.anim.run("progress", PROGRESS_MS,
                           lambda k: self.progress_bar.set(lerp(start, target, k)))
        else:
            self.anim.cancel("progress")
            self.progress_bar.set(target)

    # ---- Анимации ----

    def _busy(self):
        """Идёт переворот или слайд — новые действия игнорируем."""
        return self.anim.is_running("flip") or self.anim.is_running("slide")

    def _card_bg(self):
        """Текущий фон карточки — он же цвет, в котором «растворяется» текст."""
        current = self.card.cget("fg_color")
        if isinstance(current, str) and current.startswith("#"):
            return current
        return PALETTE[self.app.theme_name]["card_dark_bg"]

    def _word_color(self):
        """Цвет крупной надписи для текущего состояния.

        Общий источник правды для отрисовки и для анимаций: иначе анимация,
        доигрывающая после _render, красит итоговый экран не своим цветом.
        """
        p = PALETTE[self.app.theme_name]
        if self.finished:
            return p["success"]
        if not self.round:
            return p["card_dim_text"]
        return p["success"] if self.showing_answer else p["card_dark_text"]

    def _fade_side(self, k):
        """k=0 — надписи слились с фоном карточки, k=1 — видны полностью."""
        p = PALETTE[self.app.theme_name]
        bg = self._card_bg()
        dim = p["card_dim_text"]
        self.word_label.configure(text_color=mix_colors(bg, self._word_color(), k))
        self.side_label.configure(text_color=mix_colors(bg, dim, k))
        self.hint_label.configure(text_color=mix_colors(bg, dim, k))

    def toggle_answer(self):
        """Переворот карточки.

        Настоящего 3D в tkinter нет, поэтому ощущение поворота собирается из
        трёх одновременных движений: слово уменьшается в кегле (уходит в
        перспективу), растворяется в фоне карточки и сама карточка сжимается
        по ширине. На «ребре» стороны меняются местами — подмена не видна,
        потому что в этот момент текст полностью слит с фоном.
        """
        if self.finished or not self.round or self._busy():
            return

        def close(k):
            self._fade_side(1 - k)
            self.word_font.configure(size=int(round(lerp(self.WORD_SIZE, self.WORD_SIZE_MIN, k))))
            self.flip_box.place_configure(relwidth=lerp(1.0, self.FLIP_MIN_WIDTH, k))

        def open_other_side():
            self.showing_answer = not self.showing_answer
            self._render()          # тексты новой стороны...
            self._fade_side(0)      # ...но пока невидимые: проявятся во второй половине
            self.word_font.configure(size=self.WORD_SIZE_MIN)
            self.anim.run("flip", FLIP_MS // 2, unfold, easing=ease_out_cubic)

        def unfold(k):
            self._fade_side(k)
            self.word_font.configure(size=int(round(lerp(self.WORD_SIZE_MIN, self.WORD_SIZE, k))))
            self.flip_box.place_configure(relwidth=lerp(self.FLIP_MIN_WIDTH, 1.0, k))

        self.anim.run("flip", FLIP_MS // 2, close, on_done=open_other_side, easing=ease_in_cubic)

    def _slide(self, direction, apply_change):
        """Уводит карточку за край, меняет содержимое и вводит её с другой стороны."""
        # Переворот мог остаться недоигранным — распрямляем карточку и
        # перерисовываем сторону, иначе слово уедет мелким и полупрозрачным.
        self.anim.cancel("flip")
        self.flip_box.place_configure(relwidth=1.0)
        self._render()

        out_x = 0.5 - self.SLIDE_OFFSET * direction
        in_x = 0.5 + self.SLIDE_OFFSET * direction

        def leave(k):
            self.flip_box.place_configure(relx=lerp(0.5, out_x, k))
            self._fade_side(lerp(1.0, self.SLIDE_FADE, k))  # уезжая, карточка гаснет

        def enter():
            apply_change()
            self._render()
            self._render_progress()
            self.flip_box.place_configure(relx=in_x, relwidth=1.0)
            self.anim.run("slide", SLIDE_IN_MS, arrive, easing=ease_out_cubic)

        def arrive(k):
            self.flip_box.place_configure(relx=lerp(in_x, 0.5, k))
            self._fade_side(lerp(self.SLIDE_FADE, 1.0, k))

        self.anim.run("slide", SLIDE_OUT_MS, leave, on_done=enter, easing=ease_in_cubic)

    # ---- Действия пользователя ----

    def _advance(self, mark=None):
        """Отмечает текущее слово (если надо) и переходит к следующему."""
        if not self.round or self.finished or self._busy():
            return

        if mark == "known":
            word_id = self.round[self.index][0]
            move_word(word_id, LEARNED_CATEGORY)
            self.known_count += 1
            self.app.dict_tab.refresh_all()  # слово ушло в «Выучено» — обновляем словарь
        elif mark == "still":
            self.still_count += 1

        if self.index + 1 >= len(self.round):
            self._slide(1, self._mark_finished)
        else:
            self._slide(1, lambda: self._set_index(self.index + 1))

    def _set_index(self, new_index):
        self.index = new_index
        self.showing_answer = False

    def _mark_finished(self):
        self.finished = True
        self.showing_answer = False

    def handle_still(self):
        self._advance("still")

    def handle_know(self):
        self._advance("known")

    def handle_restart(self):
        """С итогового экрана — новый раунд, карточка приезжает справа."""
        if self._busy():
            return
        self._slide(1, self._reload_round)

    def go_prev(self):
        if not self.round or self.finished or self.index == 0 or self._busy():
            return
        self._slide(-1, lambda: self._set_index(self.index - 1))

    # ---- Мышь ----

    def _on_card_click(self, event=None):
        self.toggle_answer()

    def _on_card_enter(self, event=None):
        self._set_hover(True)

    def _on_card_leave(self, event=None):
        # Переход курсора на дочерний виджет тоже даёт <Leave> у родителя,
        # поэтому доверяем не событию, а реальным координатам указателя.
        self.after_idle(self._recheck_hover)

    def _recheck_hover(self):
        if not self.winfo_exists():
            return
        self._set_hover(self._pointer_over_card())

    def _pointer_over_card(self):
        try:
            px, py = self.winfo_pointerx(), self.winfo_pointery()
            x, y = self.card.winfo_rootx(), self.card.winfo_rooty()
            return x <= px < x + self.card.winfo_width() and y <= py < y + self.card.winfo_height()
        except Exception:
            return False

    def _set_hover(self, hovered):
        """Карточка под курсором чуть светлеет — тот самый «подъём» из Quizlet."""
        if hovered == self.hovered:
            return
        self.hovered = hovered
        p = PALETTE[self.app.theme_name]
        base = p["card_dark_bg"]
        current = self.card.cget("fg_color")
        start = current if isinstance(current, str) and current.startswith("#") else base
        end = mix_colors(base, p["card_dark_text"], HOVER_LIFT) if hovered else base
        self.anim.run("hover", HOVER_MS,
                       lambda k: self.card.configure(fg_color=mix_colors(start, end, k)))

    # ---- Клавиатура ----

    def _keys_active(self):
        """Шорткаты работают только на своей вкладке и мимо полей ввода."""
        if self.app.current_page != "flash":
            return False
        try:
            return not isinstance(self.app.focus_get(), tk.Entry)
        except Exception:
            return True

    def _on_key_flip(self, event=None):
        if self._keys_active():
            self.toggle_answer()

    def _on_key_next(self, event=None):
        if self._keys_active():
            self._advance()

    def _on_key_prev(self, event=None):
        if self._keys_active():
            self.go_prev()

    def _on_destroy(self, event=None):
        self.anim.cancel()


if __name__ == "__main__":
    init_db()
    app = WortschatzApp()
    app.mainloop()