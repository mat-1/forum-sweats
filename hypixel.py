import aiohttp
import random
import os

# API keys are seperated by commas
api_keys = os.getenv('keys').split(',')

s = aiohttp.ClientSession()

class PlayerNotFound(Exception): pass
class DiscordNotFound(Exception): pass

# async def get_uuid_from_ign(ign):
# 	'Returns the users Minecraft UUID based on their IGN'
# 	async with s.get(f'https://mojang-api.matdoes.dev/{ign}') as r:
# 		data = await r.json()
# 	if not data:
# 		raise PlayerNotFound(f'Invalid IGN: {ign}')
# 	return data['uuid']

async def get_user_data(ign):
	'Returns the Discord username of a Hypixel IGN'
	key = random.choice(api_keys)
	# url = f'https://api.slothpixel.me/api/players/{ign}?key={key}'
	# url = f'https://api.hypixel.net/player?key={key}&name={ign}'
	url = f'https://skyblock-api.matdoes.dev/player/{ign}?key={key}&profiles=false'
	print(url)
	async with s.get(url) as r:
		data = await r.json()
	if data.get('error'):
		print(data)
		raise PlayerNotFound(f'Invalid Hypixel player: {ign}')
	# if not data.get('player'):
	# 	print(data)
	# 	raise PlayerNotFound(f'Invalid Hypixel player: {ign}')
	return data

# async def get_discord_name(ign):
# 	'Returns the Discord username of a Hypixel IGN'
# 	# uuid = await get_uuid_from_ign(ign)
# 	key = random.choice(api_keys)
# 	# url = f'https://api.hypixel.net/player?key={key}&uuid={uuid}'
# 	url = f'https://api.slothpixel.me/api/players/{ign}?key={key}'
# 	print(url)
# 	async with s.get(url) as r:
# 		data = await r.json()
# 		# print(data)
# 	if data.get('error'):
# 		print(data)
# 		raise PlayerNotFound(f'Invalid Hypixel player: {ign}')
# 	try:
# 		discord = data['links']['DISCORD']
# 		assert discord is not None
# 		return discord
# 	except:
# 		raise DiscordNotFound()

async def get_hypixel_rank(ign):
	'Returns the Hypixel rank of an IGN'
	# uuid = await get_uuid_from_ign(ign)
	key = random.choice(api_keys)
	url = f'https://api.hypixel.net/player?key={key}&name={ign}'
	# url = f'https://api.slothpixel.me/api/players/{ign}?key={key}'
	print(url)
	async with s.get(url) as r:
		data = await r.json()
		# print(data)
	if data.get('error'):
		print(data)
		raise PlayerNotFound(f'Invalid Hypixel player: {ign}')
	rank_name = data.get('rank') or 'NON'
	rank_name = rank_name.replace('_PLUS', '+')
	return rank_name