import asyncio
import typing


from telethon.tl.types import (
    MessageEntityBankCard,
    MessageEntityBlockquote,
    MessageEntityBold,
    MessageEntityBotCommand,
    MessageEntityCashtag,
    MessageEntityCode,
    MessageEntityEmail,
    MessageEntityHashtag,
    MessageEntityItalic,
    MessageEntityMention,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityPre,
    MessageEntitySpoiler,
    MessageEntityStrike,
    MessageEntityTextUrl,
    MessageEntityUnderline,
    MessageEntityUnknown,
    MessageEntityUrl,
)


from .custom.client import MaterialClient


JSONSerializable = typing.Union[int, str, float, dict, list, set, tuple, None]


class SuperList(list):
    """
    Makes able: await self.clients.send_message("foo", "bar")
    """

    def __getattribute__(self, attr: str) -> typing.Any:
        if hasattr(list, attr):
            return list.__getattribute__(self, attr)

        for obj in self:  # TODO: find other way
            attribute = getattr(obj, attr)
            if callable(attribute):
                if asyncio.iscoroutinefunction(attribute):

                    async def foobar(*args, **kwargs):
                        return [await getattr(_, attr)(*args, **kwargs) for _ in self]

                    return foobar
                return lambda *args, **kwargs: [
                    getattr(_, attr)(*args, **kwargs) for _ in self
                ]

            return [getattr(x, attr) for x in self]


class WatcherType:
    def check(watcher):
        return hasattr(watcher, "is_watcher")


class CommandType:
    def check(command):
        return hasattr(command, "is_command")


FormattingEntity = typing.Union[
    MessageEntityUnknown,
    MessageEntityMention,
    MessageEntityHashtag,
    MessageEntityBotCommand,
    MessageEntityUrl,
    MessageEntityEmail,
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityCode,
    MessageEntityPre,
    MessageEntityTextUrl,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityCashtag,
    MessageEntityUnderline,
    MessageEntityStrike,
    MessageEntityBlockquote,
    MessageEntityBankCard,
    MessageEntitySpoiler,
]


class Module:
    """There is no help for this module."""

    strings = {"name": "Unknown"}

    def internal_init(self, client: MaterialClient, db, allmodules):
        self.allmodules = allmodules
        self.dispatcher = allmodules._dispatcher

        self.lookup = allmodules.lookup
        self.get_prefix = allmodules.get_prefix

        self._client = client
        self.client = client

        self._tg_id = client.tg_id
        self.tg_id = client.tg_id

        self._db = db
        self.db = db

    def set(self, key: str, value: JSONSerializable) -> bool:
        return self._db.set(self.__class__.__name__, key, value)

    def get(self, key: str) -> JSONSerializable:
        return self._db.get(self.__class__.__name__, key)
