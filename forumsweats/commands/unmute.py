from forumsweats.discordbot import client
from forumsweats.logs import log_unmute
from ..commandparser import Member
from ..discordbot import unmute_user
import discord

name = 'unmute'
channels = None
roles = ('helper', 'trialhelper')
args = '<member>'

def create_unmute_message(member: discord.Member, reason: str=None):
	return f'<@{member.id}> has been unmuted.'

async def run(message, member: Member):
	'Removes a mute from a member'

	await unmute_user(
		member.id,
		reason=f'Unmuted by {str(message.author)}'
	)

	await message.send(embed=discord.Embed(
		description=create_unmute_message(member)
	))
	await log_unmute(client, member, message.author, None)
