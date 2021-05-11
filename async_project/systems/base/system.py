import asyncio
import copy
import json
import logging
from abc import abstractmethod

from databases import Database

from async_project.core.eventbus import EventBus

logger = logging.getLogger("main")


class System(object):

    def __init__(self, bus: EventBus, uid: str, db, conf: dict):
        self._states = {'1': '123'}
        self.bus = bus
        self.uid = uid
        self.db: Database = db
        self.conf = conf
        self.states = {}
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        # self.bus.add_command_handler(self.on_command, f'{self.uid}')
        self.bus.add_command_handler(self.bot_menu, f'{self.uid}:bot')
        self.bus.add_command_handler(self.bot_commands, f'{self.uid}:bot_text')

    async def loads_states(self):
        with open(f'storage/{self.uid}.json', 'r') as fp:
            self.states = dict(json.load(fp))
            logger.debug('Load states from file')

    async def state_observator(self):
        last_state = self.states
        while 1:
            if self.states != last_state:
                with open(f'storage/{self.uid}.json', 'w') as fp:
                    json.dump(self.states, fp, indent=4)
            last_state = copy.deepcopy(self.states)
            await asyncio.sleep(1)

    async def send_notify(self, text):
        print(f"Система: {self.uid} - {text}")
        await self.bus.call_command('bot:notify', text)

    @abstractmethod
    async def run(self):
        pass

    @abstractmethod
    async def bot_commands(self, req):
        pass

    @abstractmethod
    async def bot_menu(self, fsm):
        pass
