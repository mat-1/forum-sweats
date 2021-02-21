from ..betterbot import Member
from ..discordbot import unmute_user
import discord

name = 'unmute'
channels = None
roles = ('helper', 'trialhelper')
args = '<member>'

async def run(message, member: Member):
	'Removes a mute from a member'

	await unmute_user(
		member.id,
		reason=f'Unmuted by {str(message.author)}'
	)

	await message.send(embed=discord.Embed(
		description=f'<@{member.id}> has been unmuted.'
	))
