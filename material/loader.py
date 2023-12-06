import typing
import logging
import sys
import os
import inspect


import importlib
import importlib.util
import importlib.machinery


from telethon import events


from . import database, dispatcher, _types, utils
from .translator import Strings
from .custom.client import MaterialClient


Module = _types.Module


logger = logging.getLogger("loader")


class Modules:
    """Material loader."""

    def __init__(
        self,
        client: MaterialClient,
        db: database.Database,
        dispatcher: dispatcher.Dispatcher,
    ) -> None:
        self._client = client
        self._db = db
        self._dispatcher = dispatcher

        self.modules = []
        self.commands = {}
        self.inline_handlers = {}

        self.aliases = {}

        self.register_core_modules()
        self.register_loaded_modules()

    async def init_dp(self) -> bool:
        """Intiliaze dispatcher."""

        self._client.add_event_handler(
            self._dispatcher.handle_event, events.NewMessage()
        )

        self._client.add_event_handler(
            self._dispatcher.handle_event, events.MessageEdited()
        )

        self._client.dp_initialized = True
        return True

    def register_core_modules(self):
        mods = filter(
            lambda x: (len(x) > 3 and x[-3:] == ".py" and x[0] != "_"),
            os.listdir(os.path.join(utils.get_base_dir(), "modules")),
        )

        for mod in mods:
            try:
                module_name = (
                    __package__ + "." + "modules" + "." + os.path.basename(mod)[:-3]
                )
                spec = importlib.util.spec_from_file_location(
                    module_name, os.path.join(utils.get_base_dir(), "modules", mod)
                )
                mod = self.register_module(spec, module_name)
                mod.internal_init(self._client, self._db, self)
            except BaseException:
                logger.exception("Failed to load module %s due to:", mod)

    def register_loaded_modules(self):
        mods = filter(
            lambda x: (len(x) > 3 and x[-3:] == ".py" and x[0] != "_"),
            os.listdir(os.path.join(utils.get_base_dir(), "loaded_modules")),
        )

        for mod in mods:
            try:
                module_name = (
                    __package__
                    + "."
                    + "loaded_modules"
                    + "."
                    + os.path.basename(mod)[:-3]
                )
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    os.path.join(utils.get_base_dir(), "loaded_modules", mod),
                )
                self.register_module(spec, module_name, "<external>")
            except BaseException:
                logger.exception("Failed to load module %s due to:", mod)

    def register_commands(self, instance: Module) -> bool:
        """Register commands from instance."""

        for command in instance.material_commands:
            if command.lower() in self.commands.keys():
                if (
                    hasattr(instance.material_commands[command], "__self__")
                    and hasattr(self.commands[command], "__self__")
                    and instance.material_commands[command].__self__.__class__.__name__
                    != self.commands[command].__self__.__class__.__name__
                ):
                    logger.error("Duplicate command %s", command)

                logger.debug("Replacing command for %r", self.commands[command])

            self.commands.update({command.lower(): instance.material_commands[command]})
            return True

    def register_inline_handlers(self, instance: Module) -> bool:
        """Register inline handlers from instance."""

        for handler in instance.material_inline_handlers:
            if handler.lower() in self.inline_handlers.keys():
                if (
                    hasattr(instance.material_inline_handlers[handler], "__self__")
                    and hasattr(self.inline_handlers[handler], "__self__")
                    and instance.material_inline_handlers[
                        handler
                    ].__self__.__class__.__name__
                    != self.inline_handlers[handler].__self__.__class__.__name__
                ):
                    logger.error("Duplicate inline handler %s", handler)

                logger.debug(
                    "Replacing inline handler for %r", self.inline_handlers[handler]
                )

            self.commands.update(
                {handler.lower(): instance.material_inline_handlers[handler]}
            )
            return True

    def register_module(
        self,
        spec: importlib.machinery.ModuleSpec,
        module_name: str,
        origin: str = "<core>",
    ) -> Module:
        """Register single module from importlib spec."""

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        ret = None

        ret = next(
            (
                value()
                for key, value in vars(module).items()
                if key.endswith("Mod") and inspect.isclass(value)
            ),
            None,
        )

        if ret is None:
            ret = module.register(module_name)
            if not isinstance(ret, Module):
                raise TypeError("Instance is not a Module, it is %r", ret)

        if origin == "<core>":
            ret.__origin__ = "<core {}>".format(module_name)
        else:
            ret.__origin__ = "<external {}>".format(module_name)

        if not hasattr(ret, "strings"):
            ret.strings = {}

        strings = Strings(ret, self._db)
        ret.strings = strings

        self.complete_registration(ret)
        self.modules += [ret]
        return ret

    def complete_registration(self, instance: Module) -> None:
        """Complete registration of instance."""

        instance.name = instance.strings["name"]

        instance.material_commands = get_commands(instance)
        instance.material_inline_handlers = get_inline_handlers(instance)

        instance.db = self._db
        instance._db = self._db

        instance.client = self._client
        instance._client = self._client

        instance.tg_id = self._client.tg_id
        instance._tg_id = self._client.tg_id

        self.register_commands(instance)
        self.register_inline_handlers(instance)

    def dispatch(self, command: str) -> list:
        """Dispatch command to appropriate module."""

        try:
            return command, self.commands[command.lower()]
        except KeyError:
            try:
                return command, self.aliases[command.lower()]
            except KeyError:
                return command, None

    def add_alias(self, command: str, func: typing.Callable) -> bool:
        """Make an alias."""

        if command.lower().split(maxsplit=1)[0] not in self.commands.keys():
            return False

        self.aliases[command.lower().split(maxsplit=1)[0]] = func
        return True

    def remove_alias(self, command: str) -> bool:
        """Remove an alias."""

        try:
            del self.aliases[command.lower().split(maxsplit=1)[0]]
            return True
        except KeyError:
            return False
        except:
            return False

    def get_prefix(self) -> str:
        """Get userbot prefix."""

        return self._db.get("dispatcher", "command_prefix", ".")

    def lookup(self, module: str) -> typing.Union[None, Module]:
        """Search module in loaded."""

        return next(
            (
                mod
                for mod in self.modules
                if mod.__class__.__name__.lower() == module.lower()
                or mod.name.lower() == module.lower()
            ),
            None,
        )


def get_commands(mod: _types.Module) -> typing.Dict:
    """Introspect the module to get its commands"""

    return {
        method_name[:-3]: getattr(mod, method_name)
        for method_name in dir(mod)
        if len(method_name) > 3
        and callable(getattr(mod, method_name))
        and method_name[-3:] == "cmd"
    }


def get_inline_handlers(mod: _types.Module) -> typing.Dict:
    """Introspect the module to get its inline handlers"""

    return {
        method_name[:-15]: getattr(mod, method_name)
        for method_name in dir(mod)
        if len(method_name) > 15
        and callable(getattr(mod, method_name))
        and method_name[-15:] == "cmd"
    }
