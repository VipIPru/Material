import difflib
import inspect
import logging


from telethon.tl.types import Message


from .. import loader, utils


class HelpMod(loader.Module):
    """Помощь по всем модулям"""

    strings = {
        "name": "Help",
        "help": ("<b>👻 {} модули</b>" "\n\n{}"),
        "module": "<b>🔸{} ( </b>{}<b> )</b>\n",
        "nodocmod": "У этого модуля нет описания",
        "nodoccmd": "У этой команды нет описания",
        "modhelp": ("<b>🔸 {}</b>" "\nℹ <b>{}</b>" "\n\n<b>Команды: </b>{}"),
        "support": "<b>Ссылка на <a href='https://t.me/MaterialUB_talks'>Support</a> чат!</b>",
    }

    def __init__(self) -> None:
        pass

    async def helpcmd(self, message: Message):
        """Список всех модулей и комманд"""

        args = utils.get_args_raw(message)

        if args:
            await self.modhelp(message, args)
            return

        text = ""
        for module in self.allmodules.modules:
            name = module.strings["name"]

            text += self.strings["module"].format(
                name,
                "<b> | </b>".join(
                    f"<code>{command}</code>"
                    for command in module.material_commands.keys()
                ),
            )

        await utils.answer(
            message, self.strings["help"].format(len(self.allmodules.modules), text)
        )

    async def modhelp(self, message: Message, args: str):
        name = args.lower()
        module = self.lookup(name)

        if not module:
            module = self.lookup(
                next(
                    (
                        reversed(
                            sorted(
                                [
                                    module.strings["name"]
                                    for module in self.allmodules.modules
                                ],
                                key=lambda x: difflib.SequenceMatcher(
                                    None,
                                    args.lower(),
                                    x,
                                ).ratio(),
                            )
                        )
                    ),
                    None,
                )
            )

        name = module.strings["name"]

        cmds = ""

        for _name, func in module.material_commands.items():
            cmds += ("\n" "<code>{}{}</code><b> - {}</b>").format(
                self._db.get("material.dispatcher", "command_prefix", "."),
                _name,
                inspect.getdoc(func) if func.__doc__ else self.strings["nodoccmd"],
            )

        await utils.answer(
            message,
            self.strings["modhelp"].format(
                name,
                inspect.getdoc(module) if module.__doc__ else self.strings["nodocmod"],
                cmds,
            ),
        )

    async def supportcmd(self, message: Message):
        """Ссылка на support чат"""
        await utils.answer(
            message,
            self.strings["support"],
        )
