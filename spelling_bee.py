import sys

import pyttsx3
from colorama import Fore, Style, init
from wonderwords import RandomWord


def get_word(max_length=8):
    r = RandomWord()
    while True:
        word = r.word(word_min_length=1, word_max_length=max_length)
        if word.isalpha():
            return word


def check_spelling(correct, attempt):
    return attempt.strip().lower() == correct.lower()


def compare(correct, attempt):
    matches = []
    for i, ch in enumerate(correct):
        if i < len(attempt) and attempt[i].lower() == ch.lower():
            matches.append(True)
        else:
            matches.append(False)
    accuracy = (sum(matches) / len(correct)) * 100
    return matches, accuracy


def speak_word(word, engine):
    engine.say(word)
    engine.runAndWait()


def format_success():
    return (
        f"{Fore.GREEN}{Style.BRIGHT}"
        f"\u2705 Congrats! You spelled it correctly!"
        f"{Style.RESET_ALL}"
    )


def format_failure(correct, matches, accuracy):
    header = f"{Fore.RED}\u274c Unlucky! The correct spelling is:{Style.RESET_ALL}\n"
    word_display = ""
    for i, ch in enumerate(correct):
        if matches[i]:
            word_display += f"{Fore.GREEN}{ch}{Style.RESET_ALL}"
        else:
            word_display += f"{Fore.RED}{Style.BRIGHT}{ch}{Style.RESET_ALL}"
    accuracy_line = f"\n{Fore.RED}Accuracy: {accuracy:.0f}%{Style.RESET_ALL}"
    return header + word_display + accuracy_line


def play_round(word, engine):
    speak_word(word, engine)
    while True:
        attempt = input("Type your spelling: ")
        if attempt.strip().lower() in ("r", "repeat"):
            speak_word(word, engine)
            continue
        break
    if check_spelling(word, attempt):
        print(format_success())
    else:
        matches, accuracy = compare(word, attempt.strip())
        print(format_failure(word, matches, accuracy))


def main():
    init()
    try:
        engine = pyttsx3.init()
    except Exception as e:
        print(f"{Fore.RED}Failed to initialise text-to-speech: {e}{Style.RESET_ALL}")
        sys.exit(1)
    print(f"{Style.BRIGHT}Welcome to Spelling Bee!{Style.RESET_ALL}\n")
    while True:
        word = get_word()
        play_round(word, engine)
        again = input("\nTry another word? (y/n): ")
        if again.strip().lower() != "y":
            print(f"\n{Style.BRIGHT}Thanks for playing! Goodbye!{Style.RESET_ALL}")
            break
        print()


if __name__ == "__main__":
    main()
