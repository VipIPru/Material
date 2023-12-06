"""Userbot logging."""

import logging


from logging.handlers import RotatingFileHandler


_main_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    style="%",
)

rotating_handler = RotatingFileHandler(
    filename="material.log",
    mode="w",
    maxBytes=10 * 1024 * 1024,
    backupCount=1,
    encoding="utf-8",
    delay=0,
)


def init():
    handler = logging.StreamHandler()

    handler.setLevel(logging.INFO)
    handler.setFormatter(_main_formatter)
    rotating_handler.setFormatter(_main_formatter)

    logging.getLogger().handlers = []
    logging.getLogger().addHandler(handler)
    logging.getLogger().addHandler(rotating_handler)
    logging.getLogger().setLevel(logging.NOTSET)

    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("pyrogram").setLevel(logging.WARNING)

    logging.captureWarnings(True)
