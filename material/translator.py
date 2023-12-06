from . import utils
from ._types import Module


class Strings:
    def __init__(self, mod: Module, db):
        self._mod = mod
        self._db = db

        self._base_strings = mod.strings

    def __getitem__(self, key: str) -> str:
        return (
            getattr(
                self._mod,
                next(
                    (
                        f"strings_{lang}"
                        for lang in self._db.get(
                            "material.translator",
                            "lang",
                            "en",
                        ).split(" ")
                        if hasattr(self._mod, f"strings_{lang}")
                        and isinstance(getattr(self._mod, f"strings_{lang}"), dict)
                        and key in getattr(self._mod, f"strings_{lang}")
                    ),
                    utils.rand(32),
                ),
                self._base_strings,
            )
        ).get(
            key,
            self._base_strings.get(key, "Unknown strings"),
        )

    def __call__(
        self,
        key: str,
    ) -> str:
        return self.__getitem__(key)

    def __iter__(self):
        return self._base_strings.__iter__()
