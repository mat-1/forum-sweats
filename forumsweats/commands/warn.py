from datetime import datetime, timedelta
from ..commandparser import Member, Time
from utils import seconds_to_string
from ..discordbot import mute_user
from forumsweats import db
import discord
import random

name = 'warn'
channels = None
pad_none = False
roles = ('helper', 'trialhelper')
args = '<member> [reason]'

USAGE_EXAMPLES = [
	'!warn badpinghere being mean to me',
	'!warn rito being really dumb'
]

async def run(message, member: Member, reason: str):
	'Warns a member. If a member is warned 3 times in a week, they are muted for 45 minutes.'

	if not member or not reason:
		return await message.channel.send(
			f'Invalid command usage. Example: **{random.choice(USAGE_EXAMPLES)}**'
		)

	if reason:
		reason = reason.strip()

	await db.add_infraction(member.id, 'warn', reason, muted_by=message.author.id)


	weekly_warns = await db.get_weekly_warns(member.id)
	description = f'<@{member.id}> has been warned for "**{reason}**".'
	if len(weekly_warns) + 1 >= 3:
		past_warn_reasons_joined = '\n'.join(map(lambda w: '- ' + w, weekly_warns))
		description += f'\nThey have been warned **{len(weekly_warns) + 1}** times in the past week, you should mute them for at least 45 minutes.\n\n**Past warn reasons**:\n{past_warn_reasons_joined}'
	await message.send(embed=discord.Embed(
		description=description
	))

	try:
		await member.send(f'You have been warned for **{reason}** by <@{message.author.id}> ({message.author})')
	except: pass



