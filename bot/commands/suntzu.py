from urllib.parse import quote_plus
import discord
import random
import json

name = 'suntzu'

with open('suntzu.json', 'r') as f:
	suntzu_quotes = json.loads(f.read())


async def run(message, extra: str = None):
	embed = discord.Embed()
	quote_text = extra or random.choice(suntzu_quotes)['text']
	embed.set_image(url='https://suntzu.matdoes.dev/quote.png?quote=' + quote_plus(quote_text))
	await message.channel.send(embed=embed)
