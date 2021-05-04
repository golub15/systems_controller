import databases

from async_project.bot import bot_main
from async_project.db import database
from async_project.config import config
from async_project.mod import *



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

logger = logging.getLogger("main")
logger.setLevel(logging.DEBUG)


class ObjectsManager:
    def __init__(self, bus, db):
        self.is_init = 1
        self.bus: EventBus = bus
        self.db: databases.Database = db

        self.data = {
            "objects": [],
            "systems": []
        }

        evb.add_command_handler(self.get_objects, 'manager:get_objects')
        evb.add_command_handler(self.get_system, 'manager:get_system')

    async def init(self):
        resp_obj = await self.db.fetch_all(query='SELECT * FROM objects')
        for x in resp_obj:
            self.data['objects'].append(x)

        resp_sys = await self.db.fetch_all(query='SELECT * FROM systems')
        for x in resp_sys:
            self.data['systems'].append(x)

        logger.debug(f"ObjectsManager: {self.data}")

    async def get_objects(self, data):
        return self.data['objects']

    async def get_system(self, obj_id):
        if obj_id is not None and type(obj_id) == str:
            return list(filter(lambda x: x[1] == int(obj_id), self.data['systems']))
        else:
            return self.data['systems']


class System:

    def __init__(self, bus: EventBus, uid: str, db, config: dict):
        self.bus = bus
        self.uid = uid
        self.db = db
        self.config = config

        self.bus.add_command_handler(self.on_command, f'{self.uid}')
        self.bus.add_command_handler(self.bot_get_commands, f'{self.uid}:bot')
        self.bus.add_command_handler(self.bot_text, f'{self.uid}:bot_text')

    async def run(self):
        pass

    async def bot_text(self, req):
        print(f'sys: {req["text"]}')

    async def bot_get_commands(self, fsm):
        # fsm
        r = {}

        if len(fsm) == 0:
            r['text'] = 'Меню системы ворот \nВыберите действие'
            r['buttons'] = [('🧩 База данных', 'db', '-1'),
                            ('🧩 Состояние', 'status', '-1')]
        elif fsm[-1][0] == 'db':
            r['text'] = 'Меню базы данных ворот \nВыберите квартиру'
            r['buttons'] = [(str(i), '*home_id', str(i)) for i in range(1, 50)]
            r['row_width'] = 8

        # btn ('Text', 'type', 'id')

        return r

    async def on_command(self, req):
        print(self.uid, 'recive_data: ', req)
        return '1234'
        pass


object_manager = ObjectsManager(evb, database)

y = System(evb, 'd0bc0609', None, None)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # loop.create_task(x.run())
    loop.run_until_complete(database.connect())
    loop.run_until_complete(object_manager.init())

    loop.create_task(bot_main())
    #loop.create_task(wsr_main())
    loop.run_forever()
