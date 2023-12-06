import copy
import logging
import asyncio
import typing
import inspect
from contextlib import suppress


from telethon import events
from telethon.tl.custom import Message
from telethon.errors import FloodWaitError, RPCError


from . import utils, database
from .custom.client import MaterialClient


class Dispatcher:
    """Dispatch all commands."""

    def __init__(self, client: MaterialClient, db: database.Database) -> None:
        self._client = client
        self._db = db
        self.logger = logging.getLogger(self.__class__.__name__)

        self.tg_id = self._client.tg_id

    async def handle_event(self, event: typing.Union[events.NewMessage, events.MessageEdited]):
        """Handle event."""

        message: Message = event.message
        prefix = self._db.get("material.dispatcher", "command_prefix", ".")
        try:
            if message.text[:1] != prefix:
                return False
        except:
            return False

        await self.handle_command(event)

    async def future_dispatcher(
        self,
        callback: typing.Awaitable,
        message: Message,
        exception_handler: typing.Awaitable,
        *args,
        **kwargs
    ) -> bool:
        """Run command."""

        try:
            await callback(message)
            return True
        except Exception as e:
            await exception_handler(e, message, *args, **kwargs)
            return False

    async def _handle_command(
        self,
        event: typing.Union[events.NewMessage, events.MessageEdited],
        watcher: bool = False,
    ) -> bool:
        """Handle messages."""

        if not hasattr(event, "message") or not hasattr(event.message, "message"):
            return False

        message: Message = event.message
        prefix = self._db.get("material.dispatcher", "command_prefix", ".")

        if message.sender_id != self.tg_id:
            return False

        if not event.message.message:
            return False

        if (
            message.out
            and len(message.message) > len(str(prefix) * 2)
            and message.message.startswith(str(prefix) * 2)
        ):
            if not watcher:
                await message.edit(
                    message.message[len(prefix) :],
                    parse_mode=lambda s: (
                        s,
                        utils.relocate_entities(
                            message.entities, -len(prefix), message.message
                        )
                        or (),
                    ),
                )
                return False

        if (
            event.sticker
            or event.dice
            or event.audio
            or event.via_bot_id
            or getattr(event, "reactions", False)
        ):
            return False
        try:
            command = message.message[len(prefix) :].strip().split(maxsplit=1)[0]
        except IndexError:
            return False

        message.message = message.message[len(prefix) :]

        txt, func = self._client.loader.dispatch(command)

        if not func:
            return False

        message.message = prefix + txt + " " + message.message[len(prefix + command) :]

        return [message, prefix, txt, func]

    async def command_exc(
        self, exception: Exception, message: Message, *args, **kwargs
    ) -> None:
        """Commands exceptions handler."""

        if isinstance(exception, RPCError):
            if isinstance(exception, FloodWaitError):
                hours = exception.seconds // 3600
                minutes = (exception.seconds % 3600) // 60
                seconds = exception.seconds % 60

                hours = "{} hours, ".format(hours) if hours else ""
                minutes = "{} minutes, ".format(minutes) if minutes else ""
                seconds = "{} seconds" if seconds else ""

                floodwait_time = "{}{}{}".format(hours, minutes, seconds)

                txt = (
                    self._client.loader.lookup("translations")
                    .strings["floodwait_error"]
                    .format(
                        utils.escape_html(message.message),
                        floodwait_time,
                        type(exception.request).__name__,
                    )
                )

            else:
                txt = (
                    self._client.loader.lookup("translations")
                    .strings["rpc_error"]
                    .format(
                        utils.escape_html(message.message),
                        exception.__class__.__name__,
                        str(exception),
                    )
                )

                with suppress(Exception):
                    await (message.edit if message.out else message.reply)(txt)

    async def handle_command(
        self, event: typing.Union[events.NewMessage, events.MessageEdited]
    ) -> bool:
        """Handle command."""

        _message = await self._handle_command(event)
        if not _message:
            return False

        message, prefix, text, command = _message

        asyncio.ensure_future(
            self.future_dispatcher(command, message, self.command_exc)
        )
