import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

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
        self._rate = None
        self._voice = None

    def set_voice_params(self, rate=None, voice=None):
        self._rate = rate
        self._voice = voice

    def say(self, word):
        self._word = word

    def runAndWait(self):
        if self._word is None:
            return
        word = self._word
        self._word = None
        for base_cmd in self._COMMANDS:
            try:
                cmd = list(base_cmd)
                if base_cmd[0] in ("espeak-ng", "espeak"):
                    if self._rate:
                        cmd.extend(["-s", str(self._rate)])
                    if self._voice:
                        cmd.extend(["-v", self._voice])
                cmd.append(word)
                subprocess.run(cmd, check=True, capture_output=True)
                return
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue


_word_cache = {}


def _fetch_word_data(word):
    """Fetch word data from the Free Dictionary API, with simple caching."""
    if word in _word_cache:
        return _word_cache[word]
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        _word_cache[word] = data
        return data
    except Exception:
        _word_cache[word] = None
        return None


def get_definition(word):
    """Return the first definition for the word, or None."""
    data = _fetch_word_data(word)
    if not data:
        return None
    try:
        return data[0]["meanings"][0]["definitions"][0]["definition"]
    except (KeyError, IndexError):
        return None


def get_sentence(word):
    """Return an example sentence for the word, or None."""
    data = _fetch_word_data(word)
    if not data:
        return None
    try:
        for meaning in data[0]["meanings"]:
            for defn in meaning["definitions"]:
                if "example" in defn:
                    return defn["example"]
    except (KeyError, IndexError):
        pass
    return None


def configure_voice(engine):
    """Configure TTS engine for a slower, friendlier female voice."""
    if isinstance(engine, SubprocessTTS):
        engine.set_voice_params(rate=130, voice="en+f3")
        return
    engine.setProperty("rate", 130)
    voices = engine.getProperty("voices")
    for voice in voices:
        if getattr(voice, "gender", None) == "Female":
            engine.setProperty("voice", voice.id)
            return


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
        print("\n1. Hear the word again")
        print("2. Get the definition")
        print("3. Hear the word in a sentence")
        print("4. Spell the word")
        choice = input("\nChoose an option: ").strip()
        if choice == "1":
            speak_word(word, engine)
        elif choice == "2":
            defn = get_definition(word)
            if defn:
                print(f"\nDefinition: {defn}")
            else:
                print("\nDefinition not available.")
        elif choice == "3":
            sentence = get_sentence(word)
            if sentence:
                print(f"\nSentence: {sentence}")
                speak_word(sentence, engine)
            else:
                print("\nSentence not available.")
        elif choice == "4":
            break
    attempt = input("Type your spelling: ")
    if check_spelling(word, attempt):
        print(format_success())
    else:
        matches, accuracy = compare(word, attempt.strip())
        print(format_failure(word, matches, accuracy))


def main():
    init()
    try:
        engine = init_tts_engine()
        configure_voice(engine)
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
