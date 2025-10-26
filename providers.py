import requests

class OnlineWordProvider:
    def __init__(self, timeout = 5):
        self.timeout = timeout
        self.last_mode: str | None = None

    def _mark(self, online: bool):
        self.last_mode = "online" if online else "offline"

    def check_online(self) -> bool:
        """
        Cheap health check. We call the dictionary API for a tiny known endpoint.
        Any 200/404 means the service is reachable.
        """
        try:
            r = requests.get(
                "https://api.dictionaryapi.dev/api/v2/entries/en/test",
                timeout=self.timeout
            )
            online = r.status_code in (200, 404)
            self._mark(online)
            return online
        except requests.RequestException:
            self._mark(False)
            return False

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
            self._mark(True)
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
            self._mark(False)
            return None
        
    def is_valid_word(self, word: str) -> bool:
        try:
            response = requests.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}",
                timeout=self.timeout
            )
            if response.status_code == 200:
                self._mark(True)
                return True
            elif response.status_code == 404:
                self._mark(True)
                return False
            
            print(f"[!] Unexpected status {response.status_code} for word: {word}")
            self._mark(True) # service reached but odd status
            return None
        except requests.exceptions.Timeout:
            print(f"[!] Timeout while validating word: {word}")
        except requests.exceptions.RequestException as e:
            print(f"[!] Network error while validating {word}: {e}")
        except Exception as e:
            print(f"[!] Unexpected error while validating {word}: {e}")
        self._mark(False)
        return None