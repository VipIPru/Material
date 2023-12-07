import os
import random
import shlex
import typing
import asyncio
import json
import time
import contextlib


from git import Repo

from datetime import timedelta
import time

from telethon.tl.custom import Message

from ._types import FormattingEntity

from telethon import events


def escape_html(text: str, /) -> str:  # sourcery skip
    """
    Pass all untrusted/potentially corrupt input here
    :param text: Text to escape
    :return: Escaped text
    """
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def get_args(message: Message) -> typing.List[str]:
    """Get arguments in message"""

    try:
        text = message.text
        if not text:
            return False

        split = text.split(" ", maxsplit=1)
        if len(split) <= 1:
            return False

        split = split[1]

        try:
            split = shlex.split(split)
        except:
            return split

        return list(filter(lambda x: len(x) > 0, split))
    except:
        return False


def get_args_raw(message: Message) -> str:
    """Get raw arguments"""

    if args := get_args(message):
        return " ".join(args)
    
    return args


def get_topic(message: Message) -> typing.Optional[int]:
    """
    Get topic id of message
    :param message: Message to get topic of
    :return: int or None if not present
    """
    return (
        (message.reply_to.reply_to_top_id or message.reply_to.reply_to_msg_id)
        if (
            isinstance(message, Message)
            or isinstance(message, Message)
            or isinstance(message, events.NewMessage.Event)
            and message.reply_to
            and message.reply_to.forum_topic
        )
        else None
    )


async def answer(message: Message, text: str, *args, **kwargs):
    """Answer message."""
    return await (message.edit if message.out else message.respond)(text, *args, **kwargs)


async def answer_file(
    message: Message,
    file: typing.Union[str, bytes],
    caption: typing.Optional[str] = None,
    **kwargs,
):
    """Answer message file."""

    if topic := get_topic(message):
        kwargs.setdefault("reply_to", topic)

    try:
        response = await message.client.send_file(
            message.peer_id,
            file,
            caption=caption,
            **kwargs,
        )
    except Exception:
        return await answer(message, caption, **kwargs)

    with contextlib.suppress(Exception):
        await message.delete()

    return response


def get_base_dir() -> str:
    """Get directory of this file"""
    return get_dir(__file__)


def get_dir(mod: str) -> str:
    """Get directory of given module"""
    return os.path.abspath(os.path.dirname(os.path.abspath(mod)))


def get_git_hash() -> typing.Union[str, bool]:
    """Get hash of last commit"""
    try:
        return Repo().head.commit.hexsha
    except Exception:
        return False


def get_git_commit_url() -> str:
    """Get URL to latest commit"""
    try:
        hash = get_git_hash()
        return f'<a href="https://github.com/Material-ub/Material/commit/{hash}">#{hash[:7]}</a>'
    except:
        return "Unknown"


def get_version() -> str:
    """Get userbot version in format x.y.z"""

    return ".".join(str(a) for a in get_version_raw())


def get_version_raw() -> typing.Tuple[int, int, int]:
    """Get raw userbot version"""
    from .version import version

    return version


def get_platform() -> str:
    """Get userbot platform"""

    IS_LUMIHOST = "LUMISHOST" in os.environ
    IS_CODESPACES = "CODESPACES" in os.environ

    if IS_LUMIHOST:
        return "😎 LumiHost"

    if IS_CODESPACES:
        return "🐈 Codespaces"

    return "💎 VDS"


def is_serializable(obj: typing.Any) -> bool:
    """Check if an object is serializable"""
    try:
        json.dumps(obj)
        return True
    except:
        return False


def rand(size: int = 6) -> str:
    """Generate string"""
    return "".join(
        [random.choice("abcdefghijklmnopqrstuvwxyz1234567890") for _ in range(size)]
    )


def relocate_entities(
    entities: typing.List[FormattingEntity],
    offset: int,
    text: typing.Optional[str] = None,
) -> typing.List[FormattingEntity]:
    """Move all entities by offset (truncating at text)"""
    length = len(text) if text is not None else 0

    for ent in entities.copy() if entities else ():
        ent.offset += offset
        if ent.offset < 0:
            ent.length += ent.offset
            ent.offset = 0
        if text is not None and ent.offset + ent.length > length:
            ent.length = length - ent.offset
        if ent.length <= 0:
            entities.remove(ent)

    return entities

def get_uptime():
    return str(timedelta(seconds=round(time.perf_counter() - init_ts)))

async def fw_protect():
    await asyncio.sleep(random.randint(1, 4))

init_ts = time.perf_counter()