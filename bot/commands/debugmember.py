from ..betterbot import Member
import discord

name = 'debugmember'


async def run(message, member: Member = None):
	await message.send(embed=discord.Embed(
		description=f'<@{member.id}>'
	))
