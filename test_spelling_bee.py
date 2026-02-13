import json
import subprocess
import pytest
from unittest.mock import MagicMock, patch, call
from colorama import Fore, Style
from spelling_bee import (
    get_word, check_spelling, compare, format_success, format_failure,
    speak_word, play_round, init_tts_engine, _find_espeak_library,
    SubprocessTTS, get_definition, get_sentence, configure_voice,
    WORD_LIST, _word_cache, _fetch_word_data,
    _FALLBACK_SENTENCES, _DEFAULT_SENTENCE,
)


# Mock API response with both definition and example sentence
_MOCK_WORD_DATA = [{
    "meanings": [{
        "definitions": [{
            "definition": "test definition",
            "example": "This is a test sentence.",
        }]
    }]
}]


class TestGetWord:
    @patch("spelling_bee._fetch_word_data", return_value=_MOCK_WORD_DATA)
    def test_returns_a_string(self, _mock):
        word = get_word()
        assert isinstance(word, str)

    @patch("spelling_bee._fetch_word_data", return_value=_MOCK_WORD_DATA)
    def test_length_at_most_8(self, _mock):
        for _ in range(50):
            word = get_word()
            assert len(word) <= 8, f"'{word}' is longer than 8 characters"

    @patch("spelling_bee._fetch_word_data", return_value=_MOCK_WORD_DATA)
    def test_length_at_least_1(self, _mock):
        for _ in range(50):
            word = get_word()
            assert len(word) >= 1, "got an empty word"

    @patch("spelling_bee._fetch_word_data", return_value=_MOCK_WORD_DATA)
    def test_is_alphabetic(self, _mock):
        for _ in range(50):
            word = get_word()
            assert word.isalpha(), f"'{word}' contains non-alpha characters"

    @patch("spelling_bee._fetch_word_data", return_value=_MOCK_WORD_DATA)
    def test_word_comes_from_word_list(self, _mock):
        for _ in range(50):
            word = get_word()
            assert word in WORD_LIST, f"'{word}' is not in the curated WORD_LIST"

    @patch("spelling_bee._fetch_word_data", return_value=None)
    def test_still_returns_word_when_api_unavailable(self, _mock):
        word = get_word()
        assert isinstance(word, str)
        assert word in WORD_LIST


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


class TestFetchWordData:
    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        _word_cache.clear()
        yield
        _word_cache.clear()

    @patch("urllib.request.urlopen", side_effect=Exception("network error"))
    def test_does_not_cache_failures(self, mock_urlopen):
        result = _fetch_word_data("testword")
        assert result is None
        assert "testword" not in _word_cache


class TestGetDefinition:
    @patch("spelling_bee._fetch_word_data", return_value=[{
        "meanings": [{"definitions": [{"definition": "a round fruit"}]}]
    }])
    def test_returns_first_definition(self, mock_fetch):
        assert get_definition("apple") == "a round fruit"

    @patch("spelling_bee._fetch_word_data", return_value=None)
    def test_returns_none_on_fetch_failure(self, mock_fetch):
        assert get_definition("apple") is None

    @patch("spelling_bee._fetch_word_data", return_value=[{"meanings": []}])
    def test_returns_none_when_no_meanings(self, mock_fetch):
        assert get_definition("apple") is None


class TestGetSentence:
    @patch("spelling_bee._fetch_word_data", return_value=[{
        "meanings": [{"definitions": [
            {"definition": "...", "example": "I ate an apple."}
        ]}]
    }])
    def test_returns_example_sentence(self, mock_fetch):
        assert get_sentence("apple") == "I ate an apple."

    @patch("spelling_bee._fetch_word_data", return_value=[{
        "meanings": [{"partOfSpeech": "noun",
                      "definitions": [{"definition": "..."}]}]
    }])
    def test_constructs_noun_fallback_when_no_example(self, mock_fetch):
        result = get_sentence("apple")
        assert "apple" in result
        assert result == _FALLBACK_SENTENCES["noun"].format(word="apple")

    @patch("spelling_bee._fetch_word_data", return_value=[{
        "meanings": [{"partOfSpeech": "verb",
                      "definitions": [{"definition": "..."}]}]
    }])
    def test_constructs_verb_fallback(self, mock_fetch):
        result = get_sentence("delegate")
        assert "delegate" in result
        assert result == _FALLBACK_SENTENCES["verb"].format(word="delegate")

    @patch("spelling_bee._fetch_word_data", return_value=[{
        "meanings": [{"partOfSpeech": "adjective",
                      "definitions": [{"definition": "..."}]}]
    }])
    def test_constructs_adjective_fallback(self, mock_fetch):
        result = get_sentence("superior")
        assert "superior" in result
        assert result == _FALLBACK_SENTENCES["adjective"].format(word="superior")

    @patch("spelling_bee._fetch_word_data", return_value=[{
        "meanings": [{"partOfSpeech": "adverb",
                      "definitions": [{"definition": "..."}]}]
    }])
    def test_constructs_adverb_fallback(self, mock_fetch):
        result = get_sentence("swiftly")
        assert "swiftly" in result
        assert result == _FALLBACK_SENTENCES["adverb"].format(word="swiftly")

    @patch("spelling_bee._fetch_word_data", return_value=None)
    def test_returns_default_fallback_on_fetch_failure(self, mock_fetch):
        result = get_sentence("apple")
        assert "apple" in result
        assert result == _DEFAULT_SENTENCE.format(word="apple")

    @patch("spelling_bee._fetch_word_data", return_value=[{
        "meanings": [
            {"definitions": [{"definition": "meaning 1"}]},
            {"definitions": [{"definition": "meaning 2", "example": "Found it!"}]}
        ]
    }])
    def test_searches_across_meanings(self, mock_fetch):
        assert get_sentence("test") == "Found it!"

    @patch("spelling_bee._fetch_word_data", return_value=[{
        "meanings": [{"partOfSpeech": "interjection",
                      "definitions": [{"definition": "..."}]}]
    }])
    def test_unknown_pos_uses_default_sentence(self, mock_fetch):
        result = get_sentence("hello")
        assert result == _DEFAULT_SENTENCE.format(word="hello")


class TestConfigureVoice:
    def test_sets_slower_rate_on_pyttsx3_engine(self):
        engine = MagicMock()
        engine.getProperty.return_value = []
        configure_voice(engine)
        engine.setProperty.assert_any_call("rate", 130)

    def test_selects_female_voice_on_pyttsx3(self):
        engine = MagicMock()
        female_voice = MagicMock()
        female_voice.gender = "Female"
        female_voice.id = "english+f3"
        engine.getProperty.return_value = [female_voice]
        configure_voice(engine)
        engine.setProperty.assert_any_call("voice", "english+f3")

    def test_skips_non_female_voices(self):
        engine = MagicMock()
        male_voice = MagicMock()
        male_voice.gender = "Male"
        male_voice.id = "english"
        engine.getProperty.return_value = [male_voice]
        configure_voice(engine)
        # Should only set rate, not voice (no female found)
        calls = [c for c in engine.setProperty.call_args_list if c[0][0] == "voice"]
        assert len(calls) == 0

    def test_sets_params_on_subprocess_tts(self):
        tts = SubprocessTTS()
        configure_voice(tts)
        assert tts._rate == 130
        assert tts._voice == "en+f3"


class TestPlayRound:
    @patch("builtins.input", side_effect=["4", "apple"])
    def test_correct_answer_prints_success(self, mock_input, capsys):
        engine = MagicMock()
        play_round("apple", engine)
        captured = capsys.readouterr()
        assert "\u2705" in captured.out
        assert Fore.GREEN in captured.out

    @patch("builtins.input", side_effect=["4", "aple"])
    def test_wrong_answer_prints_failure(self, mock_input, capsys):
        engine = MagicMock()
        play_round("apple", engine)
        captured = capsys.readouterr()
        assert "\u274c" in captured.out
        assert "%" in captured.out

    @patch("builtins.input", side_effect=["1", "4", "apple"])
    def test_option_1_repeats_word(self, mock_input):
        engine = MagicMock()
        play_round("apple", engine)
        # Initial speak + repeat = 2 calls to say
        assert engine.say.call_count == 2

    @patch("spelling_bee.get_definition", return_value="a round fruit")
    @patch("builtins.input", side_effect=["2", "4", "apple"])
    def test_option_2_shows_definition(self, mock_input, mock_def, capsys):
        engine = MagicMock()
        play_round("apple", engine)
        captured = capsys.readouterr()
        assert "a round fruit" in captured.out

    @patch("spelling_bee.get_definition", return_value=None)
    @patch("builtins.input", side_effect=["2", "4", "apple"])
    def test_option_2_handles_missing_definition(self, mock_input, mock_def, capsys):
        engine = MagicMock()
        play_round("apple", engine)
        captured = capsys.readouterr()
        assert "not available" in captured.out.lower()

    @patch("spelling_bee.get_sentence", return_value="I ate an apple.")
    @patch("builtins.input", side_effect=["3", "4", "apple"])
    def test_option_3_shows_and_speaks_sentence(self, mock_input, mock_sent, capsys):
        engine = MagicMock()
        play_round("apple", engine)
        captured = capsys.readouterr()
        assert "I ate an apple." in captured.out
        # Initial word speak + sentence speak = 2 say calls
        engine.say.assert_any_call("apple")
        engine.say.assert_any_call("I ate an apple.")

    @patch("spelling_bee.get_sentence", return_value="Please spell the word apple.")
    @patch("builtins.input", side_effect=["3", "4", "apple"])
    def test_option_3_shows_fallback_sentence(self, mock_input, mock_sent, capsys):
        engine = MagicMock()
        play_round("apple", engine)
        captured = capsys.readouterr()
        assert "Please spell the word apple." in captured.out
        engine.say.assert_any_call("Please spell the word apple.")

    @patch("builtins.input", side_effect=["4", "apple"])
    def test_speaks_word_at_start(self, mock_input):
        engine = MagicMock()
        play_round("apple", engine)
        engine.say.assert_any_call("apple")

    @patch("builtins.input", side_effect=["4", "apple"])
    def test_displays_menu_options(self, mock_input, capsys):
        engine = MagicMock()
        play_round("apple", engine)
        captured = capsys.readouterr()
        assert "1." in captured.out
        assert "2." in captured.out
        assert "3." in captured.out
        assert "4." in captured.out


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

    @patch("subprocess.run")
    def test_applies_voice_params_to_espeak(self, mock_run):
        tts = SubprocessTTS()
        tts.set_voice_params(rate=130, voice="en+f3")
        tts.say("hello")
        tts.runAndWait()
        cmd = mock_run.call_args[0][0]
        assert "-s" in cmd and "130" in cmd
        assert "-v" in cmd and "en+f3" in cmd


class TestWordList:
    """Validate the curated WORD_LIST meets basic quality requirements."""

    def test_all_words_are_alphabetic(self):
        for word in WORD_LIST:
            assert word.isalpha(), f"'{word}' contains non-alpha characters"

    def test_all_words_are_at_most_8_chars(self):
        for word in WORD_LIST:
            assert len(word) <= 8, f"'{word}' is longer than 8 characters"

    def test_has_substantial_number_of_words(self):
        assert len(WORD_LIST) >= 100

    def test_no_duplicates(self):
        assert len(WORD_LIST) == len(set(WORD_LIST)), "WORD_LIST contains duplicates"


# ---------------------------------------------------------------------------
# Realistic mock tests — verify definitions and sentences are parsed
# correctly from real API response structures for common words
# ---------------------------------------------------------------------------

# Realistic API responses matching the Free Dictionary API format
_REALISTIC_RESPONSES = {
    "happy": [{"meanings": [{"partOfSpeech": "adjective", "definitions": [
        {"definition": "Feeling or showing pleasure or contentment.",
         "example": "Melissa came in looking happy and excited."}
    ]}]}],
    "garden": [{"meanings": [{"partOfSpeech": "noun", "definitions": [
        {"definition": "A piece of ground adjoining a house, used for growing flowers.",
         "example": "The house has a beautiful garden."}
    ]}]}],
    "bridge": [{"meanings": [{"partOfSpeech": "noun", "definitions": [
        {"definition": "A structure carrying a road or path across an obstacle.",
         "example": "A bridge across the river."}
    ]}]}],
    "believe": [{"meanings": [{"partOfSpeech": "verb", "definitions": [
        {"definition": "Accept that something is true, especially without proof.",
         "example": "I believe every word he says."}
    ]}]}],
    "kitchen": [{"meanings": [{"partOfSpeech": "noun", "definitions": [
        {"definition": "A room or area where food is prepared and cooked.",
         "example": "She went into the kitchen to fix some coffee."}
    ]}]}],
    "weather": [{"meanings": [{"partOfSpeech": "noun", "definitions": [
        {"definition": "The state of the atmosphere at a particular place and time.",
         "example": "If the weather is good we can go for a walk."}
    ]}]}],
    "journey": [{"meanings": [{"partOfSpeech": "noun", "definitions": [
        {"definition": "An act of travelling from one place to another.",
         "example": "She went on a long journey across the country."}
    ]}]}],
    "ancient": [{"meanings": [{"partOfSpeech": "adjective", "definitions": [
        {"definition": "Belonging to the very distant past.",
         "example": "The ancient civilizations of the Mediterranean."}
    ]}]}],
    "provide": [{"meanings": [{"partOfSpeech": "verb", "definitions": [
        {"definition": "Make available for use; supply.",
         "example": "These clubs provide a much appreciated service."}
    ]}]}],
    "example": [{"meanings": [{"partOfSpeech": "noun", "definitions": [
        {"definition": "A thing characteristic of its kind or illustrating a rule.",
         "example": "It is a good example of how unity works."}
    ]}]}],
}

COMMON_WORDS = list(_REALISTIC_RESPONSES.keys())


def _mock_fetch(word):
    return _REALISTIC_RESPONSES.get(word)


class TestDefinitionsForCommonWords:
    """Verify definitions are correctly parsed for common words."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        _word_cache.clear()
        yield
        _word_cache.clear()

    @pytest.mark.parametrize("word", COMMON_WORDS)
    @patch("spelling_bee._fetch_word_data", side_effect=_mock_fetch)
    def test_definition_available(self, mock_fetch, word):
        defn = get_definition(word)
        assert defn is not None, f"No definition returned for '{word}'"
        assert isinstance(defn, str) and len(defn) > 0

    @pytest.mark.parametrize("word", COMMON_WORDS)
    @patch("spelling_bee._fetch_word_data", side_effect=_mock_fetch)
    def test_sentence_available(self, mock_fetch, word):
        sent = get_sentence(word)
        assert sent is not None, f"No sentence returned for '{word}'"
        assert isinstance(sent, str) and len(sent) > 0


class TestGetWordReturnsValidatedWord:
    """Verify get_word only returns words with both definition and sentence."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        _word_cache.clear()
        yield
        _word_cache.clear()

    @patch("spelling_bee.WORD_LIST", COMMON_WORDS)
    @patch("spelling_bee._fetch_word_data", side_effect=_mock_fetch)
    def test_returned_word_has_definition_and_sentence(self, mock_fetch):
        word = get_word()
        assert get_definition(word) is not None, f"'{word}' has no definition"
        assert get_sentence(word) is not None, f"'{word}' has no sentence"

    @patch("spelling_bee._fetch_word_data", return_value=_MOCK_WORD_DATA)
    def test_returned_word_is_from_word_list(self, mock_fetch):
        for _ in range(20):
            word = get_word()
            assert word in WORD_LIST


# ---------------------------------------------------------------------------
# Live integration tests — hit the real Free Dictionary API
# Skipped automatically when the API is unreachable.
# Run with: pytest -m integration
# ---------------------------------------------------------------------------

def _api_reachable():
    """Return True if the Free Dictionary API is reachable."""
    import urllib.request
    try:
        urllib.request.urlopen(
            "https://api.dictionaryapi.dev/api/v2/entries/en/hello", timeout=5
        )
        return True
    except Exception:
        return False

_skip_no_api = pytest.mark.skipif(
    not _api_reachable(),
    reason="Free Dictionary API is unreachable",
)


@pytest.mark.integration
@_skip_no_api
class TestDefinitionIntegration:
    """Verify that common words return a definition from the live API."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        _word_cache.clear()
        yield
        _word_cache.clear()

    @pytest.mark.parametrize("word", COMMON_WORDS)
    def test_definition_available(self, word):
        defn = get_definition(word)
        assert defn is not None, f"No definition returned for '{word}'"
        assert isinstance(defn, str) and len(defn) > 0


@pytest.mark.integration
@_skip_no_api
class TestSentenceIntegration:
    """Verify that common words return an example sentence from the live API."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        _word_cache.clear()
        yield
        _word_cache.clear()

    @pytest.mark.parametrize("word", COMMON_WORDS)
    def test_sentence_available(self, word):
        sent = get_sentence(word)
        assert sent is not None, f"No sentence returned for '{word}'"
        assert isinstance(sent, str) and len(sent) > 0


@pytest.mark.integration
@_skip_no_api
class TestGetWordIntegration:
    """Verify get_word returns a word with both definition and sentence."""

    @pytest.fixture(autouse=True)
    def _clear_cache(self):
        _word_cache.clear()
        yield
        _word_cache.clear()

    def test_returned_word_has_definition_and_sentence(self):
        word = get_word()
        assert get_definition(word) is not None, f"'{word}' has no definition"
        assert get_sentence(word) is not None, f"'{word}' has no sentence"
