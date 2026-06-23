"""
A.N.N. Translation Glossary Manager
Persistent glossary for consistent proper noun translations across sessions.
"""

import json
import os
from pathlib import Path

from utils.logger import get_logger

log = get_logger("glossary")

GLOSSARY_DIR = Path(__file__).parent / "glossaries"


class GlossaryManager:
    def __init__(self):
        GLOSSARY_DIR.mkdir(exist_ok=True)
        self._cache: dict[str, dict[str, str]] = {}

    def _glossary_path(self, lang: str) -> Path:
        return GLOSSARY_DIR / f"{lang}.json"

    def load(self, lang: str) -> dict[str, str]:
        if lang in self._cache:
            return self._cache[lang]

        path = self._glossary_path(lang)
        if path.exists():
            with open(path) as f:
                self._cache[lang] = json.load(f)
        else:
            self._cache[lang] = {}
        return self._cache[lang]

    def save(self, lang: str) -> None:
        path = self._glossary_path(lang)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._cache.get(lang, {}), f, ensure_ascii=False, indent=2)

    def add_term(self, lang: str, source: str, translation: str) -> None:
        glossary = self.load(lang)
        glossary[source] = translation
        self._cache[lang] = glossary
        self.save(lang)
        log.info("glossary_term_added", lang=lang, source=source, translation=translation)

    def remove_term(self, lang: str, source: str) -> bool:
        glossary = self.load(lang)
        if source in glossary:
            del glossary[source]
            self._cache[lang] = glossary
            self.save(lang)
            return True
        return False

    def get_term(self, lang: str, source: str) -> str | None:
        return self.load(lang).get(source)

    def list_terms(self, lang: str) -> dict[str, str]:
        return self.load(lang)
