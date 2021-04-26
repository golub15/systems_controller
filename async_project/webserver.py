from asyncio import *

from aiohttp import web




async def handle(request: web.Request):
    print(request.headers)

    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


app = web.Application()
app.add_routes([web.get('/{name}', handle)])


async def wsr_main():
    get_event_loop().create_task(web._run_app(app))
