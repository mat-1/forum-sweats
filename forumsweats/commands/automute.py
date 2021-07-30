from datetime import timedelta, datetime
from utils import seconds_to_string
from ..commandparser import Member
from forumsweats import db
from .mute import do_mute
from typing import Union
import discord

name = 'automute'
channels = None
pad_none = False
roles = ('helper', 'trialhelper')
args = '<member> [reason]'

infraction_keywords = {
	'spam': 60 * 30,
	'chat flood': 60 * 30,

	'nsfw': 60 * 60 * 10,

	'toxic': 60 * 60,

	'drama': 60 * 30,

	'discrimination': 60 * 60 * 24,

	'slur': 60 * 60 * 24,

	'dox': 60 * 60 * 24 * 7,

	# this catches both 'racist' and 'racism'
	'racis': 60 * 60 * 24 * 3,

	'bypassing filter': 60 * 30,
	'filter bypass': 60 * 30,

	None: 60 * 1
}


def get_mute_reason_keyword(reason) -> Union[str, None]:
	if reason is None:
		return None
	mute_length = 0
	mute_keyword = None
	for possible_keyword in infraction_keywords:
		if possible_keyword and possible_keyword in reason.lower() and infraction_keywords[possible_keyword] > mute_length:
			mute_length = infraction_keywords[possible_keyword]
			mute_keyword = possible_keyword
	return mute_keyword


def get_base_mute_length_for_infraction(reason):
	mute_keyword = get_mute_reason_keyword(reason)
	return infraction_keywords[mute_keyword]


async def guess_mute_length_for_member(member, reason):
	mute_length = 0  # will be added onto

	mute_keyword = get_mute_reason_keyword(reason)
	mute_length += get_base_mute_length_for_infraction(reason)

	# count how many times the users been muted for reasons
	# for example: { 'spam': 2, 'nsfw': 1 }
	same_infraction_counts = {}

	for infraction in await db.get_infractions(member.id):
		if infraction['type'] == 'moot': continue

		if discord.utils.utcnow() - infraction['date'] < timedelta(minutes=3):
			# if the infraction was made less than 3 minutes ago, it should be removed as it was likely an accident
			await db.clear_infraction(infraction['_id'])

		infraction_mute_keyword = get_mute_reason_keyword(infraction['reason'])
		adding_length = get_base_mute_length_for_infraction(infraction['reason'])

		if infraction_mute_keyword not in same_infraction_counts:
			same_infraction_counts[infraction_mute_keyword] = 0
		
		same_infraction_count: int = same_infraction_counts[infraction_mute_keyword] + 1
		same_infraction_counts[infraction_mute_keyword] = same_infraction_count

		if infraction_mute_keyword != mute_keyword or mute_keyword is None:
			# if the other mute was for a different reason, it can be shortened
			adding_length /= (same_infraction_count + 3)
		else:
			adding_length /= (same_infraction_count)

		print('adding', adding_length, 'seconds', same_infraction_count, infraction_mute_keyword)

		mute_length += adding_length

	return mute_length


async def run(message, member: Member, reason: str = None):
	'Automatically guess the mute length from the reason, and past infractions'

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

	await do_mute(message, member, mute_length, reason, muted_by=message.author.id)
