from .session import s
import random
import os

api_key = os.getenv('key')


class PlayerNotFound(Exception):
	pass


class DiscordNotFound(Exception):
	pass


async def get_user_data(uuid: str):
	'Returns the Discord username of a Hypixel IGN'

	if len(uuid) != 32:
		# get the uuid from https://api.mojang.com/users/profiles/minecraft/<ign>
		async with s.get(f'https://api.mojang.com/users/profiles/minecraft/{uuid}') as r:
			uuid = (await r.json())['id']

	async with s.get(f'https://api.slothpixel.me/api/players/{uuid}') as r:
		data = await r.json()
	if not data or data.get('error'):
		raise PlayerNotFound(f'Invalid Hypixel player: {uuid}')
	return data


async def get_hypixel_rank(ign: str):
	'Returns the Hypixel rank of an IGN'
	
	user_data = await get_user_data(ign)
	return user_data['rank']