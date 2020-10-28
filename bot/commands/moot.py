from ..betterbot import Member, Time
from ..discordbot import (
	has_role,
	mute_user
)
from datetime import datetime, timedelta
from utils import seconds_to_string
import discord
import db

name = 'moot'
bot_channel = False
pad_none = False

def can_moot(member):
	return (
		has_role(member.id, 717904501692170260, 'helper')
		or has_role(member.id, 717904501692170260, 'trialhelper')
	)


async def do_moot(message, member, length, reason):
	for infraction in await db.get_infractions(member.id):
		if datetime.now() - infraction['date'] < timedelta(minutes=1):
			# if the infraction was made less than 3 minutes ago, it should be removed as it was likely an accident
			await db.clear_infraction(infraction['_id'])

	await db.add_infraction(
		member.id,
		'moot',
		reason,
		length
	)

	try:
		await member.send(f'You were mooted for "**{reason}**"')
	except:
		pass

	try:
		await moot_user(
			member,
			length,
			message.guild.id if message.guild else None
		)
	except discord.errors.Forbidden:
		await message.send("I don't have permission to do this")

async def run(message, member: Member, moot_length: Time = 0, reason: str = None):
	'Moots a member for a specified amount of time'

	if not can_moot(message.author): return

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
