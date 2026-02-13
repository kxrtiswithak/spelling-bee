import subprocess
from unittest.mock import MagicMock, patch, call
from colorama import Fore, Style
from spelling_bee import (
    get_word, check_spelling, compare, format_success, format_failure,
    speak_word, play_round, init_tts_engine, _find_espeak_library,
    SubprocessTTS,
)


class TestGetWord:
    def test_returns_a_string(self):
        word = get_word()
        assert isinstance(word, str)

    def test_length_at_most_8(self):
        for _ in range(50):
            word = get_word()
            assert len(word) <= 8, f"'{word}' is longer than 8 characters"

    def test_length_at_least_1(self):
        for _ in range(50):
            word = get_word()
            assert len(word) >= 1, "got an empty word"

    def test_is_alphabetic(self):
        for _ in range(50):
            word = get_word()
            assert word.isalpha(), f"'{word}' contains non-alpha characters"


class TestCheckSpelling:
    def test_exact_match(self):
        assert check_spelling("apple", "apple") is True

    def test_case_insensitive(self):
        assert check_spelling("Apple", "apple") is True
        assert check_spelling("apple", "APPLE") is True

    def test_strips_whitespace(self):
        assert check_spelling("apple", "  apple  ") is True

    def test_mismatch_returns_false(self):
        assert check_spelling("apple", "aple") is False

    def test_empty_attempt(self):
        assert check_spelling("apple", "") is False

    def test_completely_wrong(self):
        assert check_spelling("apple", "zzzzz") is False


class TestCompare:
    def test_perfect_match(self):
        matches, accuracy = compare("apple", "apple")
        assert matches == [True, True, True, True, True]
        assert accuracy == 100.0

    def test_total_mismatch(self):
        matches, accuracy = compare("abc", "xyz")
        assert matches == [False, False, False]
        assert accuracy == 0.0

    def test_partial_match(self):
        matches, accuracy = compare("apple", "aaple")
        assert matches == [True, False, True, True, True]
        assert accuracy == 80.0

    def test_case_insensitive(self):
        matches, accuracy = compare("Apple", "apple")
        assert matches == [True, True, True, True, True]
        assert accuracy == 100.0

    def test_shorter_attempt(self):
        matches, accuracy = compare("apple", "app")
        assert matches == [True, True, True, False, False]
        assert accuracy == 60.0

    def test_longer_attempt_ignores_extra(self):
        matches, accuracy = compare("cat", "cats")
        assert matches == [True, True, True]
        assert accuracy == 100.0

    def test_empty_attempt(self):
        matches, accuracy = compare("hello", "")
        assert matches == [False, False, False, False, False]
        assert accuracy == 0.0


class TestFormatSuccess:
    def test_contains_green_ansi(self):
        output = format_success()
        assert Fore.GREEN in output

    def test_contains_check_mark_emoji(self):
        output = format_success()
        assert "\u2705" in output

    def test_contains_congratulatory_text(self):
        output = format_success()
        lower = output.lower()
        assert "congrat" in lower or "correct" in lower or "success" in lower


class TestFormatFailure:
    def test_contains_red_text(self):
        output = format_failure("apple", [True, False, True, True, True], 80.0)
        assert Fore.RED in output

    def test_contains_correct_word(self):
        output = format_failure("apple", [True, True, True, True, True], 100.0)
        assert "a" in output and "p" in output and "l" in output and "e" in output

    def test_bold_on_mismatched_chars(self):
        # 'p' at index 1 is wrong
        output = format_failure("apple", [True, False, True, True, True], 80.0)
        assert Style.BRIGHT in output

    def test_shows_accuracy_percentage(self):
        output = format_failure("apple", [True, False, True, True, True], 80.0)
        assert "80%" in output

    def test_zero_accuracy(self):
        output = format_failure("cat", [False, False, False], 0.0)
        assert "0%" in output

    def test_contains_cross_mark(self):
        output = format_failure("cat", [False, False, False], 0.0)
        assert "\u274c" in output


class TestSpeakWord:
    def test_calls_say_with_word(self):
        engine = MagicMock()
        speak_word("hello", engine)
        engine.say.assert_called_once_with("hello")

    def test_calls_run_and_wait(self):
        engine = MagicMock()
        speak_word("hello", engine)
        engine.runAndWait.assert_called_once()

    def test_say_called_before_run_and_wait(self):
        engine = MagicMock()
        call_order = []
        engine.say.side_effect = lambda w: call_order.append("say")
        engine.runAndWait.side_effect = lambda: call_order.append("runAndWait")
        speak_word("test", engine)
        assert call_order == ["say", "runAndWait"]


class TestPlayRound:
    @patch("builtins.input", return_value="apple")
    def test_correct_answer_prints_success(self, mock_input, capsys):
        engine = MagicMock()
        play_round("apple", engine)
        captured = capsys.readouterr()
        assert "\u2705" in captured.out
        assert Fore.GREEN in captured.out

    @patch("builtins.input", return_value="aple")
    def test_wrong_answer_prints_failure(self, mock_input, capsys):
        engine = MagicMock()
        play_round("apple", engine)
        captured = capsys.readouterr()
        assert "\u274c" in captured.out
        assert "%" in captured.out

    @patch("builtins.input", side_effect=["r", "apple"])
    def test_repeat_speaks_word_again(self, mock_input):
        engine = MagicMock()
        play_round("apple", engine)
        # Initial speak + repeat = 2 calls to say
        assert engine.say.call_count == 2

    @patch("builtins.input", side_effect=["repeat", "apple"])
    def test_repeat_full_word_speaks_again(self, mock_input):
        engine = MagicMock()
        play_round("apple", engine)
        assert engine.say.call_count == 2

    @patch("builtins.input", return_value="apple")
    def test_speaks_word_at_start(self, mock_input):
        engine = MagicMock()
        play_round("apple", engine)
        engine.say.assert_called_with("apple")


class TestFindEspeakLibrary:
    @patch("shutil.which", return_value=None)
    def test_returns_none_when_no_binary_found(self, mock_which):
        assert _find_espeak_library() is None

    @patch("os.path.isfile", return_value=True)
    @patch("shutil.which", side_effect=lambda b: "/data/data/com.termux/files/usr/bin/espeak-ng" if b == "espeak-ng" else None)
    def test_finds_library_via_espeak_ng_binary(self, mock_which, mock_isfile):
        result = _find_espeak_library()
        assert result is not None
        assert "/data/data/com.termux/files/usr/lib/" in result

    @patch("os.path.isfile", return_value=True)
    @patch("shutil.which", side_effect=lambda b: "/usr/local/bin/espeak" if b == "espeak" else None)
    def test_finds_library_via_espeak_binary(self, mock_which, mock_isfile):
        result = _find_espeak_library()
        assert result is not None
        assert "/usr/local/lib/" in result

    @patch("os.path.isfile", return_value=False)
    @patch("shutil.which", return_value="/usr/bin/espeak-ng")
    def test_returns_none_when_binary_exists_but_no_lib(self, mock_which, mock_isfile):
        assert _find_espeak_library() is None

    @patch("os.path.isfile", side_effect=lambda p: p.endswith("libespeak-ng.so"))
    @patch("shutil.which", side_effect=lambda b: "/prefix/bin/espeak-ng" if b == "espeak-ng" else None)
    def test_tries_multiple_lib_names(self, mock_which, mock_isfile):
        result = _find_espeak_library()
        assert result.endswith("libespeak-ng.so")


class TestInitTtsEngine:
    @patch("shutil.which", return_value="/usr/bin/aplay")
    @patch("spelling_bee.pyttsx3")
    def test_returns_engine_when_init_succeeds(self, mock_pyttsx3, mock_which):
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine
        engine = init_tts_engine()
        assert engine is mock_engine
        mock_pyttsx3.init.assert_called_once()

    @patch("shutil.which", return_value="/usr/bin/aplay")
    @patch("spelling_bee._find_espeak_library", return_value=None)
    @patch("spelling_bee.pyttsx3")
    def test_raises_when_init_fails_and_no_lib_found(self, mock_pyttsx3, mock_find, mock_which):
        mock_pyttsx3.init.side_effect = RuntimeError("eSpeak not installed")
        try:
            init_tts_engine()
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "eSpeak" in str(e)

    @patch("shutil.which", return_value="/usr/bin/aplay")
    @patch("spelling_bee._find_espeak_library", return_value="/termux/lib/libespeak-ng.so")
    @patch("spelling_bee.pyttsx3")
    def test_retries_with_patched_loader_when_lib_found(self, mock_pyttsx3, mock_find, mock_which):
        mock_engine = MagicMock()
        # First call fails, second (after patching) succeeds
        mock_pyttsx3.init.side_effect = [RuntimeError("eSpeak not installed"), mock_engine]
        engine = init_tts_engine()
        assert engine is mock_engine
        assert mock_pyttsx3.init.call_count == 2

    @patch("shutil.which", side_effect=lambda b: None if b == "aplay" else "/usr/bin/" + b)
    @patch("sys.platform", "linux")
    def test_returns_subprocess_tts_on_linux_without_aplay(self, mock_which):
        engine = init_tts_engine()
        assert isinstance(engine, SubprocessTTS)

    @patch("spelling_bee.pyttsx3")
    @patch("shutil.which", return_value="/usr/bin/aplay")
    @patch("sys.platform", "linux")
    def test_returns_pyttsx3_on_linux_with_aplay(self, mock_which, mock_pyttsx3):
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine
        engine = init_tts_engine()
        assert engine is mock_engine


class TestSubprocessTTS:
    def test_has_say_and_run_and_wait_interface(self):
        tts = SubprocessTTS()
        assert hasattr(tts, "say")
        assert hasattr(tts, "runAndWait")

    @patch("subprocess.run")
    def test_say_and_run_and_wait_calls_subprocess(self, mock_run):
        tts = SubprocessTTS()
        tts.say("hello")
        tts.runAndWait()
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "hello" in cmd

    @patch("subprocess.run", side_effect=[
        FileNotFoundError(),
        FileNotFoundError(),
        MagicMock(),
    ])
    def test_tries_next_command_on_failure(self, mock_run):
        tts = SubprocessTTS()
        tts.say("test")
        tts.runAndWait()
        assert mock_run.call_count == 3

    @patch("subprocess.run")
    def test_run_and_wait_without_say_is_noop(self, mock_run):
        tts = SubprocessTTS()
        tts.runAndWait()
        mock_run.assert_not_called()

    @patch("subprocess.run", side_effect=FileNotFoundError())
    def test_no_crash_when_all_commands_fail(self, mock_run):
        tts = SubprocessTTS()
        tts.say("word")
        tts.runAndWait()  # should not raise
