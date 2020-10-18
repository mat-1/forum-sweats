from .mute import (
	do_mute,
	can_mute
)
from ..betterbot import Member
from datetime import timedelta, datetime
from utils import seconds_to_string
import discord
import db

name = 'mute'
bot_channel = False
pad_none = False

infraction_keywords = {
	'spam': 60 * 15,
	'nsfw': 60 * 60 * 24,
	'toxic': 60 * 60,
	'drama': 60 * 30,
	'discrimination': 60 * 60 * 24 * 3,
	'slurs': 60 * 60 * 24 * 7,
	'dox': 60 * 60 * 24 * 7,
	'creepy': 60 * 60 * 24,
	'weird': 60 * 60 * 24,
	None: 60 * 1
}


def get_mute_reason_keyword(reason):
	mute_length = 0
	mute_keyword = None
	for possible_keyword in infraction_keywords:
		if possible_keyword and possible_keyword in reason.lower() and infraction_keywords[possible_keyword] > mute_length:
			mute_length = infraction_keywords[possible_keyword]
			mute_keyword = possible_keyword
	return mute_keyword


def get_mute_length_for_infraction(reason):
	mute_keyword = get_mute_reason_keyword(reason)
	return infraction_keywords[mute_keyword]


async def guess_mute_length_for_member(member, reason):
	mute_length = 0  # will be added onto

	mute_keyword = get_mute_reason_keyword(reason)
	mute_length += get_mute_length_for_infraction(reason)

	for infraction in await db.get_infractions(member.id):
		if datetime.now() - infraction['date'] < timedelta(minutes=3):
			# if the infraction was made less than 3 minutes ago, it should be removed as it was likely an accident
			await db.clear_infraction(infraction['_id'])

		infraction_mute_keyword = get_mute_reason_keyword(reason)
		adding_length = get_mute_length_for_infraction(reason)

		if infraction_mute_keyword != mute_keyword or mute_keyword is None:
			# if the other mute was for a different reason, it can be shortened
			adding_length /= 2

		mute_length += adding_length
		print('huh')

	return mute_length


async def run(message, member: Member, reason: str = None):
	'Automatically guess the mute length from the reason, and past infractions'

	if not can_mute(message.author): return

	print('pogging', member, reason)

	if not member or not reason:
		return await message.channel.send(
			'Invalid command usage. Example: **!mute gogourt 10 years nerd**'
		)

	if reason:
		reason = reason.strip()

	mute_length = await guess_mute_length_for_member(member, reason)
	mute_length_string = seconds_to_string(mute_length)

	mute_message = f'<@{member.id}> has been muted for {mute_length_string} for "**{reason}**".'

	await message.send(embed=discord.Embed(
		description=mute_message
	))

	await do_mute(message, member, mute_length, reason)
