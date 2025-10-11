# ./modules/i18n.py
import os
import json
import locale

class Localization:
    def __init__(self, lang=None, locales_dir="locales"):
        self.locales_dir = locales_dir
        self.lang = lang or self._detect_os_language()
        self._load_locale()

    def _detect_os_language(self):
        lang_code = locale.getdefaultlocale()[0]
        if lang_code:
            return lang_code[:2]
        return "en"

    def _load_locale(self):
        path = os.path.join(self.locales_dir, f"{self.lang}.json")
        if not os.path.exists(path):
            path = os.path.join(self.locales_dir, "en.json")
        with open(path, "r", encoding="utf-8") as f:
            self.translations = json.load(f)

    def t(self, key, default=None, **kwargs):
        text = self.translations.get(key, default or key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
        return text

    def set_language(self, lang):
        self.lang = lang
        self._load_locale()

# helper function
def get_localization(lang=None, locales_dir="locales"):
    return Localization(lang=lang, locales_dir=locales_dir)
