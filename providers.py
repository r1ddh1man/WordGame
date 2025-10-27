import requests

class OnlineWordProvider:
    def __init__(self, timeout = 5):
        self.timeout = timeout
        self.last_mode: str | None = None

    def get_word(self, length: int) -> str | None:
        while True:
            new_word = self.get_random_word(length)
            if self.is_valid_word(new_word):
                return new_word


    def get_random_word(self, length: int) -> str | None:
        try:
            response = requests.get(
                f"https://random-word-api.herokuapp.com/word",
                params={"length": length, "number": 1},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            word = (data[0].upper() if data and isinstance(data, list) else None)
            return word
        except requests.exceptions.Timeout:
            # API didn’t respond in time
            print(f"[!] Timeout while fetching word of length {length}")
            return None
        except requests.exceptions.RequestException as e:
            # Any other network-related error
            print(f"[!] Network error fetching word: {e}")
            return None
        except (ValueError, KeyError, IndexError, TypeError) as e:
            # JSON was invalid or in an unexpected format
            print(f"[!] Bad response format: {e}")
            return None
        
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