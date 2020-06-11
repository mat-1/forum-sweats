from aiohttp import web
import asyncio
import commands

routes = web.RouteTableDef()

@routes.get('/')
async def index(request):
	return web.Response(text='e')

def start_server(loop, background_task, client):
	#app.discord = client
	global app
	asyncio.set_event_loop(loop)
	app = web.Application(
		# middlewares=[],
		# client_max_size=4096**2
	)
	app.discord = client
	# app.add_routes([web.static('/static', 'static')])
	app.add_routes(routes)
	asyncio.ensure_future(
		background_task,
		loop=loop
	)
	web.run_app(
		app,
		port=8081
	)
