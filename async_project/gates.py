import asyncio
from async_project.eventbus import *

class Gates:

    ind = 'w23234342'

    def __init__(self):
        self.id = None
        self.db = None
        self.bus = None

    async def on_command(self, data):

        if data == 'acition_list':
            return []

        if data == 'get_db':
            return ["descr", ['buttons']]

        if data == 'get_users: ':
            return []



        pass

    async def update(self):
        pass

    async def run(self):
        print('hello')

        while 1:
            await asyncio.sleep(1)
            print('task')


        pass
