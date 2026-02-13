# spelling-bee

A spelling bee CLI tool made in Python. The tool speaks a word aloud, then challenges you to type the correct spelling.

## Requirements

- Python 3.9+
- On Linux: `espeak` must be installed (`sudo apt install espeak`)
- On macOS / Windows: no extra system dependencies

## Install

```bash
pip install -r requirements.txt
```

## Usage

```bash
python spelling_bee.py
```

- Listen to the word spoken aloud
- Type your spelling attempt and press Enter
- Type `r` or `repeat` to hear the word again
- After each word, choose to play again or quit

## Running tests

```bash
python -m pytest test_spelling_bee.py -v
```
