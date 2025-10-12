import json
import os

# Path to your locales folder
LOCALES_DIR = "locales"
LANGUAGES = ["en", "de", "pl", "jp"]

def load_json(lang):
    path = os.path.join(LOCALES_DIR, f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_localizations():
    all_keys = {}
    
    # Load keys
    for lang in LANGUAGES:
        data = load_json(lang)
        all_keys[lang] = set(data.keys())
        print(f"[INFO] Loaded {len(data)} keys for '{lang}'")

    # Reference language (English)
    ref_lang = "en"
    ref_keys = all_keys[ref_lang]

    errors = False
    for lang, keys in all_keys.items():
        missing = ref_keys - keys
        extra = keys - ref_keys
        if missing:
            print(f"[ERROR] {lang} is missing {len(missing)} keys:")
            for k in missing:
                print(f"  - {k}")
            errors = True
        if extra:
            print(f"[WARNING] {lang} has {len(extra)} extra keys:")
            for k in extra:
                print(f"  + {k}")

    if not errors:
        print("[SUCCESS] All JSONs have consistent keys!")

if __name__ == "__main__":
    validate_localizations()
