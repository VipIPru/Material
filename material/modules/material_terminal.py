import asyncio

from telethon.tl.types import Message
from .. import loader, utils

async def bash_exec(command):
    a = await asyncio.create_subprocess_shell(
        command.strip(), 
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    if not (out := await a.stdout.read(-1)):
        try:
            return (await a.stderr.read(-1)).decode()
        except UnicodeDecodeError:
            return f'Unicode decode error: {(await a.stderr.read(-1))}'
    else:
        try:
            return out.decode()
        except UnicodeDecodeError:
            return f'Unicode decode error: {out}'

class MaterialTerminalMod(loader.Module):
    """Используйте терминал BASH прямо через Material!"""
    strings = {'name': 'Terminal'}

    async def terminalcmd(self, message: Message):
        """Исползовать терминал"""
        await utils.answer(message, "👻")
        
        args = utils.get_args_raw(message)
        output = await bash_exec(args)

        await utils.answer(
            message,
            "⌨️"
            f" <b>Системная команда:</b> <code>{args}</code>\n"
            f"💾 <b>Вывод:</b>\n<code>"
            f"{output}"
            "</code>"
        )