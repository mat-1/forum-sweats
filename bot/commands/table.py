import discord
import random
import json

name = 'table'
aliases = ['tablepic', 'randomtable', 'tables']

with open('tables.json', 'r') as f:
	tables = json.loads(f.read())


async def run(message):
	url = random.choice(tables)
	embed = discord.Embed(title='Random table')
	embed.set_image(url=url)
	await message.channel.send(embed=embed)
