# Wortschatz — German Vocabulary App

A simple desktop app for learning German vocabulary. Type in a German word, it gets automatically translated to Russian and saved to your personal dictionary. Words can be sorted into categories (New / Learning / Learned), deleted, or moved between categories.

## About this project

This is a learning project. The idea, structure, and testing are mine, but the code itself was written in collaboration with an AI (Claude, by Anthropic) as part of learning to program. I intentionally went through the generated code step by step to actually understand how it works, rather than just copy-pasting a finished solution.

Technologies used:
- **Python** — main language
- **tkinter** — graphical interface (windows, tabs, buttons)
- **SQLite** — local word storage
- **deep-translator** — translation via Google Translate

## Screenshot

![App main window](image.png)![Add word tab](image-1.png)![Just Ikon](image-2.png)

## Installation & Usage

### Option 1 — just run the executable (easiest)

If the repository includes a pre-built `wortschatz.exe` (in the `dist` folder or under Releases), download it and double-click to run. No need to install Python.

## Rebuilding the .exe
 
If you change the code and want to produce a new standalone `wortschatz.exe`:
 
1. Install PyInstaller (one-time):
```
   pip install pyinstaller
```
2. Run the build command from the project folder:
```
   pyinstaller --onefile --windowed --icon="icon_3ranslate.ico" --collect-all customtkinter wortschatz.py
```
   - `--onefile` bundles everything into a single `.exe`
   - `--windowed` prevents a console window from opening alongside the app
   - `--icon="icon_3ranslate.ico"` sets the app icon (adjust the filename to match your actual icon file)
   - `--collect-all customtkinter` is required — CustomTkinter ships its theme files separately, and without this flag the built `.exe` may fail to find them on another machine
3. The finished executable appears in the `dist` folder, replacing the previous one. The `wortschatz.db` file (your saved words) is untouched by rebuilding.
If the `pyinstaller` command isn't recognized by your terminal, run it through Python instead:
```
python -m PyInstaller --onefile --windowed --icon="icon_3ranslate.ico" --collect-all customtkinter wortschatz.py
```

### Option 2 — run from source

Requires [Python 3.10+](https://www.python.org/downloads/) installed.

1. Download the repository (**Code → Download ZIP** button at the top of the page, or `git clone`)
2. Install the translation library:
   ```
   pip install deep-translator
   ```
3. Run the app:
   ```
   python wortschatz.py
   ```

## How to use

- **"Add word" tab** — type a German word and press Enter or the button. It will be translated and added to the "New" category.
- **"Dictionary" tab** — three sub-tabs by category. Select a word to delete it or move it to another category.
- All words are saved in a `wortschatz.db` file next to the program — everything persists between runs.

## Known limitations

- Translation requires an internet connection (uses Google Translate via an unofficial library).
- Categories are currently fixed (New / Learning / Learned) — custom categories aren't supported yet.
- No spell-checking — if you type a word with a typo, it will translate exactly what was typed.

## Planned features

- Web version built with Flask, to use from a smartphone
- Flashcard-style review mode
- Text-to-speech pronunciation

## Changelog v1.1

| Feature | Description |
|---|---|
| Fullscreen | Press **F11** to toggle fullscreen mode |
| Flashcards | New tab that quizzes you on words currently in the "Learning" category |
| Language switcher | Dropdown at the top of the window — switches the interface itself between Russian / English / German (doesn't affect saved words) |
| New word indicator | A red dot appears on the "Dictionary" tab when a word was added and not yet viewed |
| Automatic retry on translation errors | The app now retries a few times before showing a translation error |
| Alphabetical sorting | The "Learned" tab is now sorted alphabetically; "New" and "Learning" keep insertion order |

## Changelog v2.0
 
| Feature | Description |
|---|---|
| Redesigned interface | Full visual overhaul built with CustomTkinter, styled after my own portfolio website — dark top navigation bar, light canvas, bold-bordered cards, and color-inverted buttons |
| Light/dark theme toggle | A small button next to the language switcher flips the whole app between light and dark color schemes |
| Alphabet divider headers | The "Learned" tab now shows a header row (e.g. "A", "B") between groups of words that start with a different letter |
| Auto-capitalized entries | The first letter of both the German word and its Russian translation is capitalized automatically, even if typed in lowercase |