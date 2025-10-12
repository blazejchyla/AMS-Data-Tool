# modules/i18n.py
import json
import os

_active_loc = None  # Holds the currently active Localization object

class Localization:
    def __init__(self, lang: str, locales_dir: str = "locales"):
        self.lang = lang
        self.locales_dir = locales_dir
        self.data = {}
        self.load_file()

    def load_file(self):
        path = os.path.join(self.locales_dir, f"{self.lang}.json")
        if not os.path.isfile(path):
            print(f"[Localization] Warning: file not found: {path}")
            self.data = {}
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            print(f"[Localization] Loaded {len(self.data)} keys for '{self.lang}' from {path}")
        except Exception as e:
            print(f"[Localization] Error loading {path}: {e}")
            self.data = {}

    def get(self, key: str, fallback: str = None) -> str:
        if key in self.data:
            return self.data[key]
        else:
            print(f"[DEBUG] L(): Missing key '{key}' for language '{self.lang}'")
            return fallback if fallback is not None else key

# -------------------------------------------------------
# Global functions
# -------------------------------------------------------
def get_localization(lang: str, locales_dir: str = "locales") -> Localization:
    """Activate a localization and return the object"""
    global _active_loc
    _active_loc = Localization(lang, locales_dir)
    return _active_loc

def L(key: str, fallback: str = None, loc: Localization = None) -> str:
    """Global helper for translations; use provided loc if given."""
    loc_to_use = loc or _active_loc
    if loc_to_use is None:
        return fallback if fallback is not None else key
    return loc_to_use.get(key, fallback)

