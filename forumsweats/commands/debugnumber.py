import forumsweats.discordbot as discordbot
from forumsweats import w2n
import discord

name = 'debugnumber'
args = '[number]'


async def run(message, number: str):
	await message.channel.send(embed=discord.Embed(
        description=str(w2n.solve_expression(number))
    ))
