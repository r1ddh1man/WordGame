import requests
import time
import random
from typing import Optional


class OnlineWordProvider:
    def __init__(self, timeout: int = 5, *, max_retries: int = 10,
                 backoff_base: float = 0.5, backoff_factor: float = 1.5,
                 backoff_cap: float = 5.0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_factor = backoff_factor
        self.backoff_cap = backoff_cap
        # simple in-memory caches for validation results (per provider instance)
        self._valid_cache = set()
        self._invalid_cache = set()
        # kept for potential future use
        self.last_mode: Optional[str] = None

    def get_random_word(self, length: int) -> Optional[str]:
        """
        Fetch a random word of the given length and validate it.
        Retries with backoff up to `max_retries` times.
        """
        delay = self.backoff_base
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(
                    f"https://random-word-api.herokuapp.com/word",
                    params={"length": length, "number": 1},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                word = (data[0].upper() if data and isinstance(data, list) else None)

                if not word:
                    print("[!] Empty word received; retrying...")
                else:
                    is_valid = self.is_valid_word(word)
                    if is_valid is True:
                        return word
                    elif is_valid is False:
                        print(f"[!] Invalid word received '{word}'; retrying...")
                    else:
                        print(f"[!] Could not validate '{word}'; retrying...")

            except requests.exceptions.Timeout:
                # API didn't respond in time; retry
                print(f"[!] Timeout while fetching word of length {length}; retrying...")
            except requests.exceptions.RequestException as e:
                # Any other network-related error; retry
                print(f"[!] Network error fetching word: {e}; retrying...")
            except (ValueError, KeyError, IndexError, TypeError) as e:
                # JSON was invalid or in an unexpected format; retry
                print(f"[!] Bad response format: {e}; retrying...")

            # apply backoff before next attempt
            # jitter in [0, 0.1 * delay] to avoid thundering herd
            sleep_for = min(delay, self.backoff_cap) + random.uniform(0, 0.1 * max(delay, 0))
            time.sleep(sleep_for)
            delay = min(delay * self.backoff_factor, self.backoff_cap)

        return None
        
    def is_valid_word(self, word: str) -> Optional[bool]:
        # cache check first
        up = word.upper()
        if up in self._valid_cache:
            return True
        if up in self._invalid_cache:
            return False
        try:
            response = requests.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}",
                timeout=self.timeout
            )
            if response.status_code == 200:
                self._valid_cache.add(up)
                return True
            elif response.status_code == 404:
                self._invalid_cache.add(up)
                return False
            
            print(f"[!] Unexpected status {response.status_code} for word: {word}")
            return None
        except requests.exceptions.Timeout:
            print(f"[!] Timeout while validating word: {word}")
        except requests.exceptions.RequestException as e:
            print(f"[!] Network error while validating {word}: {e}")
        except Exception as e:
            print(f"[!] Unexpected error while validating {word}: {e}")
        return None
    
    def clear_cache(self):
        self._valid_cache.clear()
        self._invalid_cache.clear()
