from ..betterbot import Member, Time
from ..discordbot import mute_user
from datetime import datetime, timedelta
from utils import seconds_to_string
import discord
from forumsweats import db

name = 'mute'
channels = None
pad_none = False
roles = ('helper', 'trialhelper')
args = '<member> <length> [reason]'


async def do_mute(message, member, length, reason):
	for infraction in await db.get_infractions(member.id):
		if datetime.utcnow() - infraction['date'] < timedelta(minutes=1):
			# if the infraction was made less than 3 minutes ago, it should be removed as it was likely an accident
			await db.clear_infraction(infraction['_id'])

	await db.add_infraction(
		member.id,
		'mute',
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
		await mute_user(
			member,
			length,
			message.guild.id if message.guild else None
		)
	except discord.errors.Forbidden:
		await message.send("I don't have permission to do this")


async def run(message, member: Member, mute_length: Time = Time(0), reason: str = None):
	'Mutes a member for a specified amount of time. They will not be able to send any messages except in #the-gulag'

	if not member or not mute_length:
		return await message.channel.send(
			'Invalid command usage. Example: **!mute gogourt 10 years nerd**'
		)

	if reason:
		reason = reason.strip()

	mute_length_string = seconds_to_string(mute_length)

	if reason:
		mute_message = f'<@{member.id}> has been muted for {mute_length_string} for "**{reason}**".'
	else:
		mute_message = f'<@{member.id}> has been muted for {mute_length_string}.'

	await message.send(embed=discord.Embed(
		description=mute_message
	))

	await do_mute(message, member, mute_length, reason)
