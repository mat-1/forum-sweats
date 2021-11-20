import forumsweats.discordbot as discordbot
from forumsweats import numberparser
import discord

name = 'debugnumber'
args = '[number]'


async def run(message, number: str):
	await message.channel.send(embed=discord.Embed(
		description=str(numberparser.solve_expression(number))
	))
