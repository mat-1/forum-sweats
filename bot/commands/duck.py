from session import s
import discord
import random

name = 'duck'
aliases = ['duckpic', 'randomduck', 'duckpicture']
bot_channel = False


async def run(message):
	if message.channel.id not in {
		720073985412562975,  # gulag
		718076311150788649,  # bot-commands
		719518839171186698,  # staff-bot-commands
	} and message.guild: return

	show = 'duck'

	if message.channel.id == 720073985412562975:  # gulag
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
