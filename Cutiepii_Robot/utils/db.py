__all__ = ['get_collection']

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClient, AgnosticDatabase, AgnosticCollection

DB_URL = "mongodb+srv://userbot:userbot@cluster0.ltasu.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

print("Connecting to Database ...")

_MGCLIENT: AgnosticClient = AsyncIOMotorClient(DB_URL)
_RUN = asyncio.get_event_loop().run_until_complete

if "CutiepiiRobot" in _RUN(_MGCLIENT.list_database_names()):
    print("[CUTIEPII] Anime  Database Found :) => Now Logging to it...")
else:
    print("[CUTIEPII] Anime Database Not Found :( => Creating New Database...")

_DATABASE: AgnosticDatabase = _MGCLIENT["CutiepiiRobot"]


def get_collection(name: str) -> AgnosticCollection:
    """ Create or Get Collection from your database """
    return _DATABASE[name]


def _close_db() -> None:
    _MGCLIENT.close()
