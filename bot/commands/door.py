import discord
import random
import json

name = 'door'
aliases = ['doorpic', 'randomdoor', 'doors']


with open('doors.json', 'r') as f:
	doors = json.loads(f.read())


async def run(message):
	url = random.choice(doors)
	embed = discord.Embed(title='Random door')
	embed.set_image(url=url)
	await message.channel.send(embed=embed)
