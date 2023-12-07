from telethon.tl.types import Message
from datetime import timedelta
import time

from .. import loader, utils

class MaterialSettingsMod(loader.Module):
    """Настройки для твоего юзербота"""

    strings = {
        "name": "Settings"
    }

    def __init__(self) -> None:
        pass

    async def pingcmd(self, message: Message):
        """Команда для просмотра пинга."""
        start = time.perf_counter_ns()
        await utils.answer(message, "👻")

        ping = round((time.perf_counter_ns() - start) / 10**6, 3)
        uptime = str(timedelta(seconds=round(time.perf_counter() - utils.init_ts)))

        await utils.answer(
            message,
            f"👻 <b>Скорость отклика Telegram:</b> <code>{ping}</code> <b>ms</b>\n"
            f"🕓 <b>Прошло с последней перезагрузки:</b> <code>{uptime}</code>"
        )
    
    async def setprefixcmd(self, message: Message):
        """Установить префикс команд"""
        old_prefix = self._db.get("material.dispatcher", "command_prefix", ".")
        try:
            new_prefix = message.text.split()[1]
        except IndexError:
            await utils.answer(message, "❔ А какой префикс ставить то?")
        if len(new_prefix) > 1:
            await utils.answer(message, "⚠️ Префикс должен состоять только из одного символа")
            return
        
        self._db.set("material.dispatcher", "command_prefix", new_prefix)
        await utils.answer(message, "✅ Префикс обновлен. Чтобы вернуть его, используй <code>{}setprefix {}</code>".format(new_prefix, old_prefix))