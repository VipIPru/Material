import logging
import os
import json
import redis


from . import utils
from ._types import JSONSerializable
from .custom.client import MaterialClient


class Database(dict):
    """Material database."""

    def __init__(self, client: MaterialClient):
        super().__init__()
        self._client = client
        self.logger = logging.getLogger("material.database")
        self._db_path = os.path.join(
            utils.get_base_dir(),
            "database-{}.json".format(self._client.tg_id),
        )
        self._redis = None

    def get(
        self, module: str, key: str, default: JSONSerializable = None
    ) -> JSONSerializable:
        try:
            return self[module][key]
        except KeyError:
            return default

    def set(self, module: str, key: str, value: JSONSerializable):
        return self._set(module, key, value)

    def _set(self, module: str, key: str, value: JSONSerializable) -> bool:
        if not utils.is_serializable(module):
            raise TypeError(
                "Attempted to write object to "
                f"{module=} ({type(module)=}) of database. It is not "
                "JSON-serializable key which will cause errors"
            )

        if not utils.is_serializable(key):
            raise RuntimeError(
                "Attempted to write object to "
                f"{key=} ({type(key)=}) of database. It is not "
                "JSON-serializable key which will cause errors"
            )

        if not utils.is_serializable(value):
            raise RuntimeError(
                "Attempted to write object of "
                f"{key=} ({type(value)=}) to database. It is not "
                "JSON-serializable value which will cause errors"
            )

        super().setdefault(module, {})[key] = value
        return self._save()

    def _fix(self):
        db = self.copy().items()

        for key, value in db:
            if not isinstance(key, (str, int)):
                self.logger.warning(
                    "Dropped key %s because it is not string or integer", key
                )

            if not isinstance(value, dict):
                del db[key]

                self.logger.warning("Dropped key %s because it is not dict", value)

            for subkey in value:
                if not isinstance(subkey, (str, int)):
                    del db[key][subkey]
                    self.logger.warning(
                        "DbAutoFix: Dropped subkey %s of key %s, because it is not"
                        " string or integer",
                        subkey,
                        key,
                    )
                    continue

        self = db
        return True

    def _save(self) -> bool:
        # if self._redis:
        #     await self._save_redis()

        self._fix()

        try:
            with open(self._db_path, "w") as f:
                f.write(json.dumps(self))
                return True

        except Exception:
            self.logger.error("Database save failed!", exc_info=1)
            return False

    async def init(self):
        pass
