from ..betterbot import Member

from .mute import (
	do_mute,
	can_mute
)

name = 'mute'
bot_channel = False
pad_none = False


async def guess_mute_length_for_member(member, reason):
	return 60


async def run(message, member: Member, reason: str = None):
	'Automatically guess the mute length from the reason, and past infractions'

	if not can_mute(message.author): return

	if not member:
		return await message.channel.send(
			'Invalid command usage. Example: **!mute gogourt 10 years nerd**'
		)

	if reason:
		reason = reason.strip()

	length = await guess_mute_length_for_member(member, reason)

	await do_mute(message, member, length, reason)

