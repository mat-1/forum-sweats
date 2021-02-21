from ..betterbot import Member
from ..discordbot import unmoot_user
import discord

name = 'unmoot'
channels = None
roles = ('helper', 'trialhelper')
args = '<member>'

async def run(message, member: Member):
	'Removes a moot from a member'

	await unmoot_user(
		member.id,
		reason=f'Unmooted by {str(message.author)}'
	)

	await message.send(embed=discord.Embed(
		description=f'<@{member.id}> has been unmooted.'
	))
