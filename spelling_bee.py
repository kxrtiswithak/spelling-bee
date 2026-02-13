import os
import shutil
import subprocess
import sys

import pyttsx3
from colorama import Fore, Style, init
from wonderwords import RandomWord


_ESPEAK_LIB_NAMES = (
    "libespeak-ng.so",
    "libespeak-ng.so.1",
    "libespeak.so",
    "libespeak.so.1",
    "libespeak-ng.dylib",
    "libespeak-ng.1.dylib",
    "libespeak.dylib",
)


def _find_espeak_library():
    """Search for espeak shared library by inferring the lib dir from the binary location."""
    search_dirs = []
    for binary in ("espeak-ng", "espeak"):
        path = shutil.which(binary)
        if path:
            bin_dir = os.path.dirname(os.path.realpath(path))
            search_dirs.append(os.path.join(os.path.dirname(bin_dir), "lib"))
    for d in search_dirs:
        for name in _ESPEAK_LIB_NAMES:
            full_path = os.path.join(d, name)
            if os.path.isfile(full_path):
                return full_path
    return None


class SubprocessTTS:
    """Fallback TTS engine using subprocess commands directly.

    Used when pyttsx3's audio backend is unavailable (e.g. no aplay on Termux).
    Provides the same say()/runAndWait() interface as a pyttsx3 engine.
    """

    _COMMANDS = [
        ["espeak-ng"],
        ["espeak"],
        ["termux-tts-speak"],
    ]

    def __init__(self):
        self._word = None

    def say(self, word):
        self._word = word

    def runAndWait(self):
        if self._word is None:
            return
        word = self._word
        self._word = None
        for base_cmd in self._COMMANDS:
            try:
                subprocess.run(
                    base_cmd + [word],
                    check=True,
                    capture_output=True,
                )
                return
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue


def init_tts_engine():
    """Initialize TTS engine with fallback for non-standard platforms.

    On Linux, pyttsx3's espeak driver plays audio via aplay (ALSA).
    If aplay is not available (e.g. Termux on Android), returns a
    SubprocessTTS that calls espeak-ng/espeak/termux-tts-speak directly.
    """
    # pyttsx3's espeak driver hardcodes os.system("aplay ...") for Linux
    # playback. If aplay is missing, audio silently fails, so skip pyttsx3
    # entirely and use SubprocessTTS which calls TTS commands directly.
    if sys.platform.startswith("linux") and not shutil.which("aplay"):
        return SubprocessTTS()

    try:
        return pyttsx3.init()
    except Exception as original_error:
        lib_path = _find_espeak_library()
        if lib_path is None:
            raise original_error

        import ctypes

        # Remove cached failed imports so pyttsx3 retries the driver load
        for mod_name in list(sys.modules):
            if "pyttsx3.drivers" in mod_name:
                del sys.modules[mod_name]

        # Temporarily patch ctypes.cdll.LoadLibrary so pyttsx3's espeak
        # driver can find the library at the non-standard path
        original_load = ctypes.cdll.LoadLibrary

        def _patched_load(name):
            try:
                return original_load(name)
            except OSError:
                if "espeak" in str(name).lower():
                    return original_load(lib_path)
                raise

        ctypes.cdll.LoadLibrary = _patched_load
        try:
            return pyttsx3.init()
        finally:
            ctypes.cdll.LoadLibrary = original_load


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
        engine = init_tts_engine()
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
