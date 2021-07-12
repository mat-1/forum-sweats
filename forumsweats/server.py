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

cached_users = {}

@routes.get('/api/leaderboard/bobux')
async def api_bobux(request):
	bobux_leaderboard_raw = await discordbot.db.get_bobux_leaderboard(100)
	bobux_leaderboard = []
	for member in bobux_leaderboard_raw:
		user = discordbot.client.get_user(member['discord']) or cached_users.get(member['discord'])
		if not user:
			try: user = await discordbot.client.fetch_user(member['discord'])
			except: user = '???'
			cached_users[member['discord']] = user
		bobux_leaderboard.append({
			'bobux': member['bobux'],
			'id': member['discord'],
			'name': str(user),
			'avatar': user.avatar_url_as(size=256).url if user != '???' else None,
		})
	return web.json_response(bobux_leaderboard)

@routes.get('/api/leaderboard/activitybobux')
async def api_activitybobux(request):
	bobux_leaderboard_raw = await discordbot.db.get_activity_bobux_leaderboard(100)
	bobux_leaderboard = []
	for member in bobux_leaderboard_raw:
		user = discordbot.client.get_user(member['discord']) or cached_users.get(member['discord'])
		if not user:
			try: user = await discordbot.client.fetch_user(member['discord'])
			except: user = '???'
			cached_users[member['discord']] = user
		bobux_leaderboard.append({
			'bobux': member['bobux'],
			'id': member['discord'],
			'name': str(user),
			'avatar': user.avatar_url_as(size=256).url if user != '???' else None,
		})
	return web.json_response(bobux_leaderboard)


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
