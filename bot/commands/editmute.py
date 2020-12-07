from ..betterbot import Member, Time
from ..discordbot import (
	has_role,
	mute_user
)
from datetime import datetime, timedelta
from utils import seconds_to_string
import discord
import db

name = 'editmute'
channels = None
pad_none = False


def can_mute(member):
	return (
		has_role(member.id, 'helper')
		or has_role(member.id, 'trialhelper')
	)


async def do_mute(message, member, length, reason):
	try:
		await mute_user(
			member,
			length,
			message.guild.id if message.guild else None
		)
	except discord.errors.Forbidden:
		await message.send("I don't have permission to do this")


async def run(message, member: Member, mute_length: Time = 0, reason: str = None):
	'Changes the mute length of a user without adding a new infraction'

	if not can_mute(message.author): return

	if not member or not mute_length:
		return await message.channel.send(
			'Invalid command usage. Example: **!editmute gogourt 10 years accidentally entered a length that was too short**'
		)

	if reason:
		reason = reason.strip()

	mute_length_string = seconds_to_string(mute_length)

	if reason:
		changed_message = f'<@{member.id}>\'s mute has been extended to {mute_length_string} for "**{reason}**"'
		dm_changed_message = f'Your mute has been extended to {mute_length_string} for "**{reason}**"'
	else:
		changed_message = f'<@{member.id}>\'s mute has been extended to {mute_length_string}'
		dm_changed_message = f'Your mute has been extended to {mute_length_string}'

	try:
		await member.send(
			dm_changed_message
		)
	except discord.errors.Forbidden:
		pass
	
	await message.send(embed=discord.Embed(
		description=changed_message
	))

	await do_mute(message, member, mute_length, reason)
