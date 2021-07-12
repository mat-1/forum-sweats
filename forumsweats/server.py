from forumsweats import db
from . import discordbot
from aiohttp import web
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

@routes.get('/api/bobux')
async def api_bobux(request):
	return web.json_response(await db.get_bobux_leaderboard(100))

@routes.get('/api/activitybobux')
async def api_activitybobux(request):
	return web.json_response(await db.get_activity_bobux_leaderboard(100))


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
