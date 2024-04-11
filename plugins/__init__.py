#(©)Codexbotz
#@iryme
# https://www.youtube.com/channel/UC7tAa4hho37iNv731_6RIOg




from aiohttp import web
from .route import routes


async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app
