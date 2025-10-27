# wordgame.py
# Optimized, GUI-ready engine for the "common letters" word game
# Rules:
# - User chooses a word length N.
# - A secret word of length N is chosen at random from a big dictionary.
# - Player has 20 attempts to guess words of the same length.
# - Feedback after each (valid) guess = number of UNIQUE letters in common
#   with the secret (duplicates in the guess count only once).
# - Example: secret="MISS", guess="MASK" -> common letters {M, S} -> 2
#
# This module is UI-agnostic (no input/print in core logic).
# You can import WordGame in a GUI, or run the CLI at the bottom for quick play.

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union
from providers import OnlineWordProvider


# -------------------------
# Utilities
# -------------------------

_WORD_RE = re.compile(r"^[A-Za-z]+$")


def _normalize_words(raw: str) -> List[str]:
    """
    Parse the dictionary content into a list of uppercase words.
    Supports *any* whitespace separators (space or newline).
    """
    # Split on any whitespace; keep alphabetic-only tokens
    words = [w.upper() for w in raw.split() if _WORD_RE.match(w)]
    return words


def build_by_length(words: Iterable[str]) -> Dict[int, List[str]]:
    """
    Build a map of {length: [WORDS]} for O(1) access to a given length bucket.
    """
    by_len: Dict[int, List[str]] = {}
    for w in words:
        by_len.setdefault(len(w), []).append(w)
    return by_len


def unique_common_letters(a: str, b: str) -> int:
    """
    Unique-letter overlap count, case-insensitive.
    Example: MISS vs MASK -> {M,S} -> 2
    """
    return len(set(a.upper()) & set(b.upper()))


# -------------------------
# Game Engine
# -------------------------

@dataclass
class GuessResult:
    valid: bool
    message: str = ""
    common: Optional[int] = None  # number of unique letters in common (when valid)


@dataclass
class WordGame:
    # words_by_length: Dict[int, List[str]]
    max_attempts: int = 20
    provider: Optional[OnlineWordProvider] = None

    # internal state (set on new_game)
    length: Optional[int] = None
    secret: Optional[str] = None
    attempts_left: int = field(default=0, init=False)
    status: str = field(default="idle", init=False)  # "idle" | "playing" | "won" | "lost"
    _history: List[Dict[str, object]] = field(default_factory=list, init=False)

    # ------------- lifecycle -------------

    def new_game(self, length: int) -> "WordGame":
        """
        Start a new round for a given word length.
        Online-only: requires an `OnlineWordProvider` and does not fall back
        to local dictionaries.
        """
        if length <= 0:
            raise ValueError("Please choose a positive word length.")
        
        self.length = length
        secret: Optional[str] = None

        if self.provider is None:
            raise ValueError("Online provider not configured. Cannot start a game.")

        try:
            secret = self.provider.get_word(length)
        except Exception:
            secret = None

        if not secret:
            raise ValueError(
                f"Unable to fetch an online word of length {length}. Check your internet connection and try again."
            )

        self.secret = secret.upper()
        self.attempts_left = self.max_attempts
        self.status = "playing"
        self._history.clear()
        return self

    # ------------- gameplay -------------

    def guess(self, word: str) -> GuessResult:
        """
        Submit a guess. Returns a GuessResult with `common` when valid.
        - Valid guess: A-Z only, exactly self.length letters,
          (optionally) present in dictionary when require_in_dictionary=True.
        - Valid guesses consume an attempt and update history/status.
        - Invalid guesses do NOT consume attempts.
        """
        if self.status != "playing":
            return GuessResult(valid=False, message="Start a new game first.")

        if self.length is None or self.secret is None:
            return GuessResult(valid=False, message="Game not initialized.")

        guess = (word or "").strip().upper()

        # Validate characters
        if not guess:
            return GuessResult(valid=False, message="Please enter a guess.")
        if not _WORD_RE.match(guess):
            return GuessResult(valid=False, message="Use letters A–Z only.")

        # Validate length
        if len(guess) != self.length:
            return GuessResult(
                valid=False,
                message=f"Please enter exactly {self.length} letters."
            )
        
        # check if this guess was already made
        for h in self._history:
            if h["guess"] == guess:
                return GuessResult(valid=False, message=f'You already guessed "{guess}". Try again.')

        # ONLINE ONLY validation
        if self.provider is None:
            return GuessResult(valid=False, message="Online dictionary unavailable.")

        try:
            is_valid: Optional[bool] = self.provider.is_valid_word(guess)
        except Exception:
            is_valid = None

        if is_valid is None:
            return GuessResult(valid=False, message="Could not validate the word online. Please try again.")
        if not is_valid:
            return GuessResult(valid=False, message=f'"{guess}" is not in the dictionary.') 

        # Compute feedback (valid guess → consumes attempt)
        common = unique_common_letters(guess, self.secret)
        self.attempts_left -= 1

        # Update history
        self._history.append({"guess": guess, "common": common})

        # Win / lose checks
        if guess == self.secret:
            self.status = "won"
        elif self.attempts_left <= 0:
            self.status = "lost"

        return GuessResult(valid=True, message="", common=common)

    # ------------- accessors -------------

    def history(self) -> List[Dict[str, object]]:
        return list(self._history)


# -------------------------
# Loading helpers
# -------------------------

def load_words_file(path: Path) -> List[str]:
    """
    Load words from a text file. Supports one-word-per-line OR space-separated.
    """
    raw = path.read_text(encoding="utf-8", errors="ignore")
    return _normalize_words(raw)


def load_engine_from_file(path: Path, *, max_attempts: int = 20) -> WordGame:
    """
    Convenience: load words, build buckets, and return a ready engine.
    """
    words = load_words_file(path)
    by_len = build_by_length(words)
    return WordGame(max_attempts=max_attempts)


# -------------------------
# Optional: tiny CLI for quick testing
# -------------------------

def _cli():
    """
    Quick terminal game for manual testing (kept minimal):
    - Run:  python wordgame.py words.txt
    """
    import sys
    from providers import OnlineWordProvider

    # if len(sys.argv) < 2:
    #     print("Usage: python wordgame.py <words_file>")
    #     sys.exit(1)

    # path = Path(sys.argv[1])
    engine = WordGame() # load_engine_from_file(path)

    engine.provider = OnlineWordProvider(timeout=5)

    print("Welcome to the Common-Letters Word Game!")
    while True:
        try:
            length = int(input("Choose word length: ").strip())
            engine.new_game(length)
        except ValueError as e:
            print(f"[!] {e}")
            continue
        break

    print(f"OK! I chose a {engine.length}-letter word. You have {engine.max_attempts} attempts.")
    while engine.status == "playing":
        g = input("Your guess: ").strip()
        res = engine.guess(g)  # always validated online first, then local
        if not res.valid:
            print(f"[!] {res.message}")
            continue

        print(f"Common letters: {res.common} | Attempts left: {engine.attempts_left}")

        if engine.status == "won":
            print("You got it! 🎉")
        elif engine.status == "lost":
            print(f"Out of attempts. The word was: {engine.secret}")

    # show a short history
    print("History:")
    for i, h in enumerate(engine.history(), start=1):
        print(f"{i:2d}. {h['guess']} → {h['common']}")


if __name__ == "__main__":
    _cli()
