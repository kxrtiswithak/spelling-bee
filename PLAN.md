# Spelling Bee CLI — Implementation Plan

## Overview
A Python CLI tool that speaks a word aloud via text-to-speech, then prompts the user to type the correct spelling. Feedback is colour-coded with accuracy details on failure.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pyttsx3` | Offline text-to-speech (uses espeak on Linux, SAPI5 on Windows, nsss on macOS) |
| `colorama` | Cross-platform coloured/bold terminal output |
| `wonderwords` | Offline random English word generation with min/max length filtering |
| `pytest` | Test framework for TDD workflow |

A `requirements.txt` file will pin these dependencies.

---

## File Structure

```
spelling-bee/
├── requirements.txt          # pyttsx3, colorama, wonderwords, pytest
├── spelling_bee.py           # main CLI entry point + all game logic
├── test_spelling_bee.py      # tests (TDD — written before implementation)
├── README.md                 # (already exists — will update with usage instructions)
└── .gitignore                # (already exists)
```

> **Why a flat structure?** The tool is small enough that a single module plus a test file is sufficient. No package/`src` layout needed.

---

## Word Generation (`wonderwords`)

Instead of a hardcoded local word list, use the `wonderwords` library to generate random real English words filtered by length:

```python
from wonderwords import RandomWord

r = RandomWord()
word = r.word(word_min_length=1, word_max_length=8)
```

This is **future-proof** — changing the length constraint is a single parameter change, no curated lists to maintain. The library works entirely offline with its own bundled dictionary.

---

## Main Script (`spelling_bee.py`)

### Flow

```
1. Pick a random word via wonderwords (≤ 8 chars)
2. Speak the word aloud (pyttsx3) — word is NOT printed
3. Prompt: "Type your spelling: "
4. Quick equality check first (case-insensitive) → if exact match, skip to success
5. If no match, run detailed char-by-char comparison for accuracy & diff
6. Print result (success or failure with details)
7. Ask if the user wants another word — loop or exit
```

### Step-by-step detail

#### 1. Initialisation
- `colorama.init()` for cross-platform ANSI support.
- `pyttsx3.init()` to create TTS engine (done once, reused across rounds).

#### 2. Word selection
- `RandomWord().word(word_min_length=1, word_max_length=8)` via wonderwords.

#### 3. Speaking the word
- `engine.say(word)` followed by `engine.runAndWait()`.
- Offer a "repeat" option: if the user types `r` or `repeat` instead of an answer, speak the word again before accepting input.

#### 4. Input & comparison
- `input("Type your spelling: ")` — strip whitespace.
- **Fast path:** simple case-insensitive equality check (`attempt.lower() == correct.lower()`). If it matches, jump straight to success output — no need to run character-by-character logic.
- **Slow path (mismatch only):** run the detailed `compare()` function to get positional matches and accuracy percentage.

#### 5a. Correct answer
- Print a message like:
  ```
  ✅ Congrats! You spelled it correctly!
  ```
  in **bright green** text (`Fore.GREEN + Style.BRIGHT`).

#### 5b. Incorrect answer
- Print a message like:
  ```
  ❌ Unlucky! The correct spelling is:
  ```
  in **red** text.

- **Show the correct word with incorrect letters in bold:**
  - Align the user's attempt against the correct word character-by-character.
  - Letters the user got right → normal green.
  - Letters the user got wrong (mismatch or missing) → **bold red**.
  - Example — correct: `giraffe`, typed: `jirafe`:
    ```
    g i r a f f e
    ^         ^
    ```
    `g` and the second `f` would be bold red; the rest normal green.

- **Percentage accuracy:**
  - `accuracy = (matching_chars / len(correct_word)) * 100`
  - Displayed as e.g. `Accuracy: 71%`
  - Matching is positional — compare index by index. Characters beyond the shorter string count as mismatches.

#### 6. Loop
- Prompt: `"Try another word? (y/n): "`
- `y` → go to step 2; anything else → exit with a goodbye message.

---

## Accuracy & Diff Logic (detail)

**Fast path** — checked first, before any character work:

```python
def check_spelling(correct: str, attempt: str) -> bool:
    """Simple equality check (case-insensitive). Returns True if correct."""
    return attempt.strip().lower() == correct.lower()
```

**Slow path** — only called when `check_spelling` returns `False`:

```python
def compare(correct: str, attempt: str) -> tuple[list[bool], float]:
    """
    Returns:
      - A list of booleans (one per char in `correct`) — True if that
        position matches, False otherwise.
      - Accuracy as a float 0–100.
    """
    matches = []
    for i, ch in enumerate(correct):
        if i < len(attempt) and attempt[i].lower() == ch.lower():
            matches.append(True)
        else:
            matches.append(False)
    accuracy = (sum(matches) / len(correct)) * 100
    return matches, accuracy
```

When printing the correct word after a wrong answer, iterate through `correct` and `matches`:
- Match → `Fore.GREEN + char`
- Mismatch → `Fore.RED + Style.BRIGHT + char` (bold red)

---

## Edge Cases to Handle

| Case | Handling |
|------|----------|
| Empty input | Treat as fully wrong (0% accuracy) |
| Input longer than correct word | Extra characters ignored; accuracy based on correct word length only |
| Input shorter than correct word | Missing positions count as wrong |
| Non-alpha characters in input | Accept as-is, they'll simply mismatch |
| TTS engine fails to init | Print a clear error and exit (e.g. espeak not installed on Linux) |

---

## TDD Approach & Implementation Order

Development follows **test-driven development**: write failing tests first, then implement just enough code to make them pass. Tests are run after every implementation step — **no step proceeds until all tests are green and the app builds without errors.**

### Phase 1 — Project setup
1. Create `requirements.txt` (pyttsx3, colorama, wonderwords, pytest)
2. Install dependencies
3. Create empty `spelling_bee.py` and `test_spelling_bee.py`
4. **Run tests** — verify pytest discovers the test file (0 tests, no errors)

### Phase 2 — Word generation
5. Write tests for `get_word()`: returns a string, length ≤ 8, is alphabetic
6. Implement `get_word()` using wonderwords
7. **Run tests** — all green before continuing

### Phase 3 — Spelling check (fast path)
8. Write tests for `check_spelling()`: exact match, case-insensitive match, whitespace handling, mismatch returns False
9. Implement `check_spelling()`
10. **Run tests** — all green before continuing

### Phase 4 — Detailed comparison (slow path)
11. Write tests for `compare()`: perfect match returns all True + 100%, total mismatch returns all False + 0%, partial match returns correct booleans + correct %, shorter input, longer input, empty input
12. Implement `compare()`
13. **Run tests** — all green before continuing

### Phase 5 — Output formatting
14. Write tests for `format_success()`: contains green ANSI codes, contains check mark emoji, contains congratulatory text
15. Write tests for `format_failure()`: contains red text, contains correct word, bold on mismatched chars, shows accuracy percentage
16. Implement `format_success()` and `format_failure()`
17. **Run tests** — all green before continuing

### Phase 6 — TTS integration
18. Write tests for `speak_word()`: mock pyttsx3 engine, verify `say()` and `runAndWait()` are called with the correct word
19. Implement `speak_word()`
20. **Run tests** — all green before continuing

### Phase 7 — Game loop & CLI
21. Write tests for the game loop: mock input/TTS, verify correct flow for right answer, wrong answer, repeat request, quit
22. Implement the main game loop with input handling
23. **Run tests** — all green before continuing

### Phase 8 — Polish
24. Update `README.md` with install & usage instructions
25. Final full test run + manual smoke test
