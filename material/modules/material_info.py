from telethon.tl.types import Message

from .. import loader, utils


class MaterialInfoMod(loader.Module):
    """Информация твоего юзербота"""

    strings = {
        "name": "Info",
        "owner": "Owner",
        "version": "Version",
        "build": "Build",
        "prefix": "Prefix",
        "uptime": "Uptime",
        "branch": "Branch",
    }

    def __init__(self) -> None:
        pass

    async def infocmd(self, message: Message):
        """Показать информацию юзерота"""

        prefix = self._db.get("material.dispatcher", "command_prefix", ".")
        me = await self._client.get_me()
        name = me.first_name
        await utils.answer(
            message,
            """
👻 Material

Владелец: {}
Версия: 0.1.0
Префикс: « {} »

        """.format(name, prefix),
        )
