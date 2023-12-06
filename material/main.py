import os
import argparse

import random

import typing
import logging

import sqlite3
import asyncio

from getpass import getpass
from telethon.sessions import MemorySession, SQLiteSession

from telethon.network.connection import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.network.connection import ConnectionTcpFull

from telethon.errors import (
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    AuthKeyDuplicatedError,
)

from . import utils, configurator, _types, loader, database, dispatcher

from .custom.client import MaterialClient


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mtproxy-host",
        dest="mtproxy_host",
        action="store",
        help="MTProxy host, without port",
    )
    parser.add_argument(
        "--mtproxy-port",
        dest="mtproxy_port",
        action="store",
        type=int,
        help="MTProxy port",
    )
    parser.add_argument(
        "--mtproxy-secret",
        dest="mtproxy_secret",
        action="store",
        help="MTProxy secret",
    )
    args = parser.parse_args()
    return args


class Material:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

        try:
            self.loop = asyncio.get_event_loop()
        except:
            self.loop = asyncio.new_event_loop()

        self.args = parse_args()
        self.clients = _types.SuperList()
        self.sessions = []
        self.tokens = []
        self.badge_called = False
        self._get_proxy()

    def _get_tokens(self):
        """Get API ID and Hash from environment and 'tokens.txt' file."""

        try:
            with open(
                os.path.join(
                    utils.get_base_dir(),
                    "api_tokens.txt",
                ),
                "r",
            ) as f:
                self.tokens = [l.strip() for l in f.readlines()]
                return True

        except FileNotFoundError:
            try:
                self.tokens = [
                    os.environ["API_ID"],
                    os.environ["API_HASH"],
                ]
                return True
            except:
                self.tokens = []
                return False

        return False

    def _get_proxy(self) -> bool:
        """Get proxy parameters from arguments (--mtproxy-host, --mtproxy-port, --mtproxy-secret)"""

        if (
            self.args.mtproxy_host is not None
            and self.args.mtproxy_port is not None
            and self.args.proxy_secret is not None
        ):
            self.logger.debug(
                "Using proxy %s:%s",
                self.args.mtproxy_host,
                self.args.mtproxy_port,
            )

            self.proxy, self.connection = (
                (
                    self.args.mtproxy_host,
                    self.args.mtproxy_port,
                    self.args.mtproxy_secret,
                ),
                ConnectionTcpMTProxyRandomizedIntermediate,
            )
            return True

        self.proxy, self.connection = None, ConnectionTcpFull

        # Proxy parameters are not specified
        # But we will return True anyway

        return True

    def _get_sessions(self) -> typing.Union[bool, None]:
        """Get sessions from disk."""

        self.sessions = []
        self.sessions += [
            SQLiteSession(
                os.path.join(
                    utils.get_base_dir(),
                    session.rsplit(".session", 1)[0],
                )
            )
            for session in filter(
                lambda fn: fn.startswith("material-") and fn.endswith(".session"),
                os.listdir(
                    utils.get_base_dir(),
                ),
            )
        ]
        return True

    async def _save_session(self, client: MaterialClient):
        """Save new session"""

        if hasattr(client, "tg_id"):
            tg_id = client.tg_id
        else:
            me = await client.get_me()
            client.tg_id = me.id
            client.mt_me = me
            tg_id = me.id

        session = SQLiteSession(
            os.path.join(
                utils.get_base_dir(),
                "material-{}".format(tg_id),
            )
        )

        session.set_dc(
            client.session.dc_id,
            client.session.server_address,
            client.session.port,
        )

        session.auth_key = client.session.auth_key

        session.save()
        client.session = session

        client.database = database.Database(client)  # type: ignore
        await client.database.init()

    def _setup_client(self) -> bool:
        """Install userbot and create session."""

        try:
            phone = input("Enter your phone number: ")
            client = MaterialClient(
                MemorySession(),
                self.tokens[0],
                self.tokens[1],
                connection=self.connection,
                proxy=self.proxy,
                device_model="Material on {}".format(
                    utils.get_platform().split(maxsplit=1)[1]
                ),
                app_version="Material v{}".format(utils.get_version()),
            )

            client.start(phone, lambda: getpass("Enter your 2FA password: "))

            asyncio.ensure_future(self._save_session(client))

            self.clients += [client]
            return True

        except (EOFError, OSError):
            raise

    def _init_clients(self):
        """Initialize all sessions."""

        for session in self.sessions.copy():
            try:
                client = MaterialClient(
                    session,
                    self.tokens[0],
                    self.tokens[1],
                    connection=self.connection,
                    proxy=self.proxy,
                    device_model="Material on {}".format(
                        utils.get_platform().split(maxsplit=1)[1]
                    ),
                    app_version="Material v{}".format(utils.get_version()),
                )

                client.start(
                    lambda: input("Enter your phone number: "),
                    lambda: getpass("Enter your 2FA password: "),
                )

                client.phone = "1337"

                self.clients += [client]
            except sqlite3.OperationalError:
                self.logger.error(
                    "Check that this is the only instance running. "
                    "If that doesn't help, delete the file '%s'",
                    session.filename,
                )
                continue

            except (TypeError, AuthKeyDuplicatedError):
                os.remove(os.path.join(utils.get_base_dir(), session.filename))
                self.sessions.remove(session)
            except (ValueError, ApiIdInvalidError):
                configurator.setup_api()
                return False
            except PhoneNumberInvalidError:
                self.logger.error("Invalid phone number!")
                self.sessions.remove(session)

        return bool(self.clients)

    def _get_api_tokens(self):
        tokens = self._get_tokens()

        if not tokens:
            configurator.setup_api()
            return self._get_api_tokens()

        return tokens

    async def _badge(self, client: MaterialClient):
        """Async main for client"""
        try:
            req = "Update required"
            tg_id = client.tg_id

            logo = """
                              _                   _           _ 
              /\/\     __ _  | |_    ___   _ __  (_)   __ _  | |
             /    \   / _` | | __|  / _ \ | '__| | |  / _` | | |
            / /\/\ \ | (_| | | |_  |  __/ | |    | | | (_| | | |
            \/    \/  \__,_|  \__|  \___| |_|    |_|  \__,_| |_|
                                                    
            • Build: {}
            • Version: {}
            • {}
            • Platform: {}
            """

            if not self.badge_called:
                print(
                    logo.format(
                        "Unknown",
                        utils.get_version(),
                        req,
                        utils.get_platform(),
                    )
                )
                self.badge_called = True

            self.logger.info("- Material started for %s -", tg_id)
            return True
        except Exception:
            self.logger.error("Badge error...")
            return False

    async def amain(self, first: bool, client: MaterialClient):
        """Async main for client"""

        client.parse_mode = "HTML"
        await client.start()

        self.logger.info("Loading database...")

        client.db = database.Database(client)

        self.logger.info("Loading dispatcher...")

        client.dp = dispatcher.Dispatcher(client, client.db)

        self.logger.info("Loading modules...")

        client.loader = loader.Modules(client, client.db, client.dp)

        await client.loader.init_dp()

        self.logger.info("Successful init")

        if first:
            await self._badge(client)

        await client.run_until_disconnected()
        return True

    async def amain_wrapper(self, client: MaterialClient):
        """Wrapper around amain"""

        async with client:
            first = True
            me = await client.get_me()
            client.tg_id = me.id
            client.mt_me = me
            while await self.amain(first, client):
                first = False

    def _loop(self):
        loops = [self.amain_wrapper(client) for client in self.clients]
        self.loop.run_until_complete(asyncio.gather(*loops))

    def main(self):
        self._get_api_tokens()
        self._get_sessions()

        if (
            not self.clients and not self.sessions or not self._init_clients()
        ) and not self._setup_client():
            return

        self.loop.set_exception_handler(
            lambda _, x: logging.error(
                "Exception on event loop! %s",
                x["message"],
                exc_info=x.get("exception", None),
            )
        )

        self._loop()


material = Material()
