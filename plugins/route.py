#(©)Codexbotz
#rymme
# https://www.youtube.com/@ultroidofficial




from aiohttp import web

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("ultroid_official")
