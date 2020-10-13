from ..betterbot import Member, Time
from ..discordbot import (
	has_role,
	mute_user
)
import discord
import db

name = 'mute'
bot_channel = False


async def run(message, member: Member, length: Time = 0, reason: str = None):
	'Mutes a member for a specified amount of time'

	if not (
		has_role(message.author.id, 717904501692170260, 'helper')
		or has_role(message.author.id, 717904501692170260, 'trialhelper')
	): return

	if not member or not length:
		return await message.channel.send(
			'Invalid command usage. Example: **!mute gogourt 10 years nerd**'
		)

	if reason:
		reason = reason.strip()

	if reason:
		mute_message = f'<@{member.id}> has been muted for "**{reason}**".'
	else:
		mute_message = f'<@{member.id}> has been muted.'

	await message.send(embed=discord.Embed(
		description=mute_message
	))

	await db.add_infraction(
		member.id,
		'mute',
		reason
	)

	try:
		await member.send(f'You were muted for "**{reason}**"')
	except:
		pass

	try:
		await mute_user(
			member,
			length,
			message.guild.id if message.guild else None
		)
	except discord.errors.Forbidden:
		await message.send("I don't have permission to do this")
