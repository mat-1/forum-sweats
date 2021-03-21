from ..commandparser import Member, Time
from ..discordbot import moot_user
from datetime import datetime, timedelta
from utils import seconds_to_string
import discord
from forumsweats import db

name = 'moot'
channels = None
pad_none = False
roles = ('helper', 'trialhelper')
args = '<member> <length> [reason]'


async def do_moot(message, member, length, reason):
	await db.add_infraction(
		member.id,
		'moot',
		reason,
		length
	)

	mute_length_string = seconds_to_string(length)

	try:
		if reason:
			await member.send(f'You were muted for {mute_length_string} for "**{reason}**"')
		else:
			await member.send(f'You were muted for {mute_length_string}')
	except discord.errors.Forbidden:
		pass

	try:
		await moot_user(
			member,
			length,
			message.guild.id if message.guild else None
		)
	except discord.errors.Forbidden:
		await message.send("I don't have permission to do this")


async def run(message, member: Member, moot_length: Time = Time(0), reason: str = None):
	'"Moots" (joke mutes) a member for a specified amount of time. '\
	'They will still have all their normal permissions, but will have a gray name and access to the #the-mootlag'

	if not member or not moot_length:
		return await message.channel.send(
			'Invalid command usage. Example: **!moot gogourt 10 years nerd**'
		)

	if reason:
		reason = reason.strip()

	moot_length_string = seconds_to_string(moot_length)

	if reason:
		moot_message = f'<@{member.id}> has been mooted for {moot_length_string} for "**{reason}**".'
	else:
		moot_message = f'<@{member.id}> has been mooted for {moot_length_string}.'

	await message.send(embed=discord.Embed(
		description=moot_message
	))

	await do_moot(message, member, moot_length, reason)
