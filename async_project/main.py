from async_project.bot import bot_main
from async_project.eventbus import evb
from async_project.mod import *
from async_project.webserver import wsr_main


class System:

    def __init__(self, bus: EventBus, uid: str, db, config: dict):
        self.bus = bus
        self.uid = uid
        self.db = db
        self.config = config

        self.bus.add_command_handler(self.on_command, f'{self.uid}')

    async def run(self):
        pass

    async def on_command(self, req):
        print(self.uid, 'recive_data: ', req)
        return '1234'
        pass


class ObjectsManager:

    def __init__(self):
        self.systems = []


y = System(evb, '4f31d2', None, None)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # loop.create_task(x.run())
    loop.create_task(bot_main())
    loop.create_task(wsr_main())
    loop.run_forever()
