import asyncio
import logging

from async_project.core.db import database
from async_project.core.eventbus import evb
from async_project.core.manager import ObjectsManager
from async_project.systems.bot.bot import bot_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()
object_manager = ObjectsManager(evb, database, loop)

if __name__ == '__main__':
    loop.run_until_complete(database.connect())

    loop.create_task(object_manager.run())
    loop.create_task(bot_main())

    loop.run_forever()
