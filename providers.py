import requests


class OnlineWordProvider:
    def __init__(self, timeout = 5):
        self.timeout = timeout
        self.last_mode: str | None = None

    def get_random_word(self, length: int) -> str | None:
        """
        Fetch a random word of the given length and validate it.
        Repeats fetching until a word passes validation, then returns it.
        """
        while True:
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
                    continue

                if self.is_valid_word(word):
                    return word
                else:
                    print(f"[!] Invalid word received '{word}'; retrying...")
                    continue

            except requests.exceptions.Timeout:
                # API didn't respond in time; retry
                print(f"[!] Timeout while fetching word of length {length}; retrying...")
                continue
            except requests.exceptions.RequestException as e:
                # Any other network-related error; retry
                print(f"[!] Network error fetching word: {e}; retrying...")
                continue
            except (ValueError, KeyError, IndexError, TypeError) as e:
                # JSON was invalid or in an unexpected format; retry
                print(f"[!] Bad response format: {e}; retrying...")
                continue
        
    def is_valid_word(self, word: str) -> bool:
        try:
            response = requests.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}",
                timeout=self.timeout
            )
            if response.status_code == 200:
                return True
            elif response.status_code == 404:
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

