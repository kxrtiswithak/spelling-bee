from unittest.mock import MagicMock, patch
from colorama import Fore, Style
from spelling_bee import get_word, check_spelling, compare, format_success, format_failure, speak_word, play_round


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
