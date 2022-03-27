from typing import Union
from . import discordbot
from aiohttp import web
import asyncio
import discord
import config
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

	main_guild = discordbot.client.get_guild(config.main_guild)
	if not main_guild:
		return web.json_response({ 'error': 'main guild not found' })

	for member in bobux_leaderboard_raw:
		_user = main_guild.get_member(member['discord']) or discordbot.client.get_user(member['discord']) or cached_users.get(member['discord'])
		if not _user:
			try: user = await discordbot.client.fetch_user(member['discord'])
			except: user = '???'
			cached_users[member['discord']] = user
		else:
			user = _user
		user: Union[discord.User, discord.Member, str]
		bobux_leaderboard.append({
			'bobux': member['bobux'],
			'id': member['discord'],
			'username': user.name if not isinstance(user, str) else 'Deleted user',
			'discrim': user.discriminator if not isinstance(user, str) else '0000',
			'avatar': str(user.display_avatar.with_format('png').with_size(128).url) if not isinstance(user, str) else None,
			'color': str(user.color) if not isinstance(user, str) else '#e5f7f7'
		})
	return web.json_response(bobux_leaderboard)

@routes.get('/api/leaderboard/activitybobux')
async def api_activitybobux(request):
	bobux_leaderboard_raw = await discordbot.db.get_activity_bobux_leaderboard(100)
	bobux_leaderboard = []
	main_guild = discordbot.client.get_guild(config.main_guild)
	if not main_guild:
		return web.json_response({ 'error': 'main guild not found' })

	for member in bobux_leaderboard_raw:
		user = main_guild.get_member(member['discord']) or discordbot.client.get_user(member['discord']) or cached_users.get(member['discord'])
		if not user:
			try: user = await discordbot.client.fetch_user(member['discord'])
			except: user = '???'
			cached_users[member['discord']] = user
		bobux_leaderboard.append({
			'bobux': member['activity_bobux'],
			'id': member['discord'],
			'username': user.name if not isinstance(user, str) else 'Deleted user',
			'discrim': user.discriminator if not isinstance(user, str) else '0000',
			'avatar': str(user.display_avatar.with_format('png').with_size(128).url) if not isinstance(user, str) else None,
			'color': str(user.color) if not isinstance(user, str) else '#e5f7f7'
		})
	return web.json_response(bobux_leaderboard)


async def start_server(loop, background_task, client):
	global app
	# asyncio.set_event_loop(loop)
	app = web.Application(
	)
	discordbot.ticket_types = await discordbot.db.get_ticket_types()
	app.discord = client
	app.add_routes(routes)
	asyncio.ensure_future(
		await background_task(),
		loop=loop
	)
	web.run_app(
		app,
		port=8081
	)
