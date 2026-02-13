# Spelling Bee CLI — Implementation Plan

## Overview
A Python CLI tool that speaks a word aloud via text-to-speech, then prompts the user to type the correct spelling. Feedback is colour-coded with accuracy details on failure.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pyttsx3` | Offline text-to-speech (uses espeak on Linux, SAPI5 on Windows, nsss on macOS) |
| `colorama` | Cross-platform coloured/bold terminal output |

A `requirements.txt` file will pin these two dependencies.

---

## File Structure

```
spelling-bee/
├── requirements.txt          # pyttsx3, colorama
├── words.py                  # curated word list (common English words, ≤ 8 chars)
├── spelling_bee.py           # main CLI entry point + all game logic
├── README.md                 # (already exists — will update with usage instructions)
└── .gitignore                # (already exists)
```

> **Why a flat structure?** The tool is small enough that a single module plus a word list is sufficient. No package/`src` layout needed.

---

## Word List (`words.py`)

- A Python list of ~100–150 common English words, each **≤ 8 characters**.
- Mix of difficulty: easy ("apple", "house") through to moderate ("rhythm", "giraffe").
- Stored as a plain `WORDS = [...]` constant so it can be imported directly — no external file parsing, no internet required.

---

## Main Script (`spelling_bee.py`)

### Flow

```
1. Import word list, pick a random word
2. Speak the word aloud (pyttsx3) — word is NOT printed
3. Prompt: "Type your spelling: "
4. Compare user input (case-insensitive) to the correct word
5. Print result (success or failure with details)
6. Ask if the user wants another word — loop or exit
```

### Step-by-step detail

#### 1. Initialisation
- `colorama.init()` for cross-platform ANSI support.
- `pyttsx3.init()` to create TTS engine (done once, reused across rounds).

#### 2. Word selection
- `random.choice(WORDS)` from the curated list.

#### 3. Speaking the word
- `engine.say(word)` followed by `engine.runAndWait()`.
- Offer a "repeat" option: if the user types `r` or `repeat` instead of an answer, speak the word again before accepting input.

#### 4. Input
- `input("Type your spelling: ")` — strip whitespace, compare case-insensitively.

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

## Summary of Tasks

1. Create `requirements.txt` with `pyttsx3` and `colorama`
2. Create `words.py` with curated word list (≤ 8 chars each)
3. Create `spelling_bee.py` with:
   - TTS initialisation
   - Random word selection
   - Speak-the-word function
   - User input with "repeat" support
   - Correct/incorrect result display (green tick / red cross, bold mismatched letters, accuracy %)
   - Play-again loop
4. Update `README.md` with install & usage instructions
