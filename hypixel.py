import aiohttp
import random
import os

# API keys are seperated by commas
api_keys = os.getenv('keys').split(',') if os.getenv('keys') else []

s = aiohttp.ClientSession()


class PlayerNotFound(Exception):
	pass


class DiscordNotFound(Exception):
	pass


async def get_user_data(ign):
	'Returns the Discord username of a Hypixel IGN'
	key = random.choice(api_keys)
	url = f'https://skyblock-api.matdoes.dev/player/{ign}?key={key}&profiles=false'
	print(url)
	async with s.get(url) as r:
		data = await r.json()
	if data.get('error'):
		print(data)
		raise PlayerNotFound(f'Invalid Hypixel player: {ign}')
	return data


async def get_hypixel_rank(ign):
	'Returns the Hypixel rank of an IGN'
	key = random.choice(api_keys)
	url = f'https://api.hypixel.net/player?key={key}&name={ign}'
	print(url)
	async with s.get(url) as r:
		data = await r.json()
	if data.get('error'):
		print(data)
		raise PlayerNotFound(f'Invalid Hypixel player: {ign}')
	rank_name = data.get('rank') or 'NON'
	rank_name = rank_name.replace('_PLUS', '+')
	return rank_name