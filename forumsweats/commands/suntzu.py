from urllib.parse import quote_plus
import discord
import random
import json

name = 'suntzu'
args = '[quote]'

with open('suntzu.json', 'r') as f:
	suntzu_quotes = json.loads(f.read())

async def run(message, quote: str = None):
	'Generates an image with sun tzu saying your quote (or a random quote)'

	embed = discord.Embed()
	quote_text = quote or random.choice(suntzu_quotes)['text']
	embed.set_image(url='https://suntzu.matdoes.dev/quote.png?quote=' + quote_plus(quote_text))
	await message.channel.send(embed=embed)
