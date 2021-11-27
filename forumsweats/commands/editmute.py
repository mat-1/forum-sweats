from ..commandparser import Member, Time
from ..discordbot import mute_user
from utils import seconds_to_string
import discord
from forumsweats import db
import time

name = 'editmute'
channels = None
pad_none = False
roles = ('helper', 'trialhelper')
args = '<member> <length> [reason]'


async def do_edit_mute(message, member, length):
	try:
		await mute_user(
			member,
			length,
			message.guild.id if message.guild else None,
		)
	except discord.errors.Forbidden:
		await message.send("I don't have permission to do this")


async def run(message, member: Member, mute_length: Time = Time(0)):
	'Changes the mute length of a user without adding a new infraction'

	if not member or not mute_length:
		return await message.channel.send(
			'Invalid command usage. Example: **!editmute gogourt 10 years**'
		)

	mute_length_string = seconds_to_string(mute_length)

	changed_message = f'<@{member.id}>\'s mute has been changed to {mute_length_string}'
	dm_changed_message = f'Your mute has been changed to {mute_length_string}'

	mute_remaining = int((await db.get_mute_end(member.id)) - time.time())

	if mute_remaining < 0:
		return await message.channel.send('That user isn\'t muted')
	else:
		try:
			await member.send(dm_changed_message)
		except discord.errors.Forbidden:
			pass
	
		await message.send(embed=discord.Embed(
			description=changed_message
		))

		await do_edit_mute(message, member, mute_length)
