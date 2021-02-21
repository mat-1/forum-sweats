from session import s
import random
import os

# API keys are seperated by commas
api_key = os.getenv('key')


class PlayerNotFound(Exception):
	pass


class DiscordNotFound(Exception):
	pass


async def get_user_data(ign):
	'Returns the Discord username of a Hypixel IGN'
	url = f'https://skyblock-api2.matdoes.dev/player/py5'
	async with s.get(
		url,
		headers={
			'key': api_key
		}
	) as r:
		data = await r.json()
	if not data or data.get('error'):
		raise PlayerNotFound(f'Invalid Hypixel player: {ign}')
	return data


async def get_hypixel_rank(ign):
	'Returns the Hypixel rank of an IGN'
	
	user_data = await get_user_data(ign)
	return user_data['player']['rank']['name']