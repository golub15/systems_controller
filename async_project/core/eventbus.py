import asyncio
import logging

logger = logging.getLogger('evb')
logger.setLevel(logging.DEBUG)


class EventBus:

    def __init__(self, id):
        self.status = True
        self.sub = []
        self.commands_handlers = {}

    def add_command_handler(self, func, name):

        logger.debug(f"Added handler: {name}")

        self.commands_handlers[name] = func

    async def call_command(self, name, data):

        if name in self.commands_handlers:
            return await self.commands_handlers[name](data)
        else:
            logger.error(f"Handler: {name} not found")
            return None

    def subscribe(self, func, topic):
        self.sub.append((topic, func))

    def get_event(self, topic):

        def actual_decorator(func):
            self.sub.append((topic, func))

        return actual_decorator

    async def fire(self, topic, payload):

        for t, p in self.sub:
            if t == topic:
                await asyncio.get_event_loop().create_task(p(payload))


evb = EventBus('123')
