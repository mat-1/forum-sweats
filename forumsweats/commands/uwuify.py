from forumsweats import uwuify
import discord

name = 'uwuify'
aliases = ('owoify', 'uwu', 'owo')
args = '[phrase]'


async def run(message, phrase: str):
	await message.channel.send(embed=discord.Embed(
        description=uwuify.uwuify(phrase)
    ))
