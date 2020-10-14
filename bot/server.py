from aiohttp import web
from . import discordbot, commands
import asyncio
import os


routes = web.RouteTableDef()


@routes.get('/')
async def index(request):
	return web.Response(text='e')


@routes.get('/kill')
async def kill_bot(request):
	if request.query.get('token') == os.getenv('token'):
		exit()
	return web.Response(text='e')


@routes.get('/api/members')
async def api_members(request):
	return web.json_response(discordbot.api_get_members())


def start_server(loop, background_task, client):
	global app
	asyncio.set_event_loop(loop)
	app = web.Application(
	)
	app.discord = client
	app.add_routes(routes)
	asyncio.ensure_future(
		background_task,
		loop=loop
	)
	web.run_app(
		app,
		port=8081
	)
