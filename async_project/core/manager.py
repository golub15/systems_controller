import asyncio
import json
import logging

from databases import Database

from async_project.core.eventbus import EventBus
from async_project.systems.gates.gates import Gates

logger = logging.getLogger("main")


class ObjectsManager:
    def __init__(self, bus, db, lp: asyncio.AbstractEventLoop):
        self.is_init = 1
        self.bus: EventBus = bus
        self.db: Database = db
        self.loop = lp

        self.data = {
            "objects": [],
            "systems": []
        }

        self.systems_objects = []

        self.bus.add_command_handler(self.get_objects, 'manager:get_objects')
        self.bus.add_command_handler(self.get_system, 'manager:get_system')

    async def init(self):

        with open(f'storage/systems.json', 'r', encoding='utf-8') as fp:
            systems = dict(json.load(fp))
            logger.debug('Load global configs from file')

            for k, v in systems['objects'].items():
                self.data['objects'].append((k, v))

            for k, v in systems['systems'].items():
                # logger.debug(f"ObjectsManager: {k} - {v}")
                self.data['systems'].append((k, v['type'], v['object_id'], v['title']))

                system = None
                if v['type'] == 'Gates':
                    system = Gates(self.bus, k, self.db, v)
                else:
                    logger.error(f'System type: {v["type"]} not found')

                if system is not None:
                    logger.info(f'System add {v["type"]}, id: {k}')
                    self.systems_objects.append(system)

    async def run(self):

        await self.init()

        for i in self.systems_objects:
            self.loop.create_task(i.run())

    async def get_objects(self, data):
        return self.data['objects']

    async def get_system(self, obj_id):
        if obj_id is not None and type(obj_id) == str:
            return list(map(lambda x: (x[0], x[3]), filter(lambda x: x[2] == obj_id, self.data['systems'])))
        else:
            return self.data['systems']
