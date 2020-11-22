from bot import config
from session import s
import discord
import random

name = 'duck'
aliases = ['duckpic', 'randomduck', 'duckpicture']
channels = ('bot-commands', 'gulag')


async def run(message):
	show = 'duck'

	if message.channel.id == config.channels['gulag']:
		show = random.choice(['duck', 'no'])

	if show == 'duck':
		async with s.get('https://random-d.uk/api/random') as r:
			data = await r.json()
			url = data['url']
	else:
		url = 'https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4a9.png'
	embed = discord.Embed(title='Random duck')
	embed.set_image(url=url)
	await message.channel.send(embed=embed)
