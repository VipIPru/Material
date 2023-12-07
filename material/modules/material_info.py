from telethon.tl.types import Message

from .. import loader, utils


class MaterialInfoMod(loader.Module):
    """Информация твоего юзербота"""

    strings = {
        "name": "Info",
        "banner_url": "https://0x0.st/H3Kw.jpg",
        "message.text": "👻 Material\n\n👤 Владелец: {owner}\n\n⚙️ Версия: {version} {build}\n\n⌨️ Префикс: « {prefix} »\n🕔 Аптайм: {uptime}\n\n{platform}",
    }

    def __init__(self) -> None:
        pass

    async def infocmd(self, message: Message):
        """Показать информацию юзерота"""

        inf = {
            "owner": "",
            "version": "",
            "build": "",
            "prefix": ".",
            "uptime": "",
            "platform": "",
        }

        # Owner
        try:
            me = await self._client.get_me()
            name = me.first_name
            inf["owner"] = name
        except:
            pass

        # Version
        try:
            inf["version"] = utils.get_version()
        except:
            pass

        # Build
        try:
            inf["build"] = utils.get_git_commit_url()
        except:
            pass

        # Prefix
        try:
            inf["prefix"] = self.get_prefix()
        except:
            pass

        # Uptime
        try:
            inf["uptime"] = utils.get_uptime()
        except:
            pass

        # Platform
        try:
            inf["platform"] = utils.get_platform()
        except:
            pass

        # Answer File.
        await utils.answer_file(
            message,
            self.strings["banner_url"],
            self.strings["message.text"].format(**inf),
        )
