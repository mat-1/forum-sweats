from utils import confirmed_emoji
from ..betterbot import Member
from forumsweats import db

name = 'clearrecentinfraction'
aliases = ('clearnewinfraction',)
channels = None
roles = ('helper', 'trialhelper')
args = ('<member>')


async def run(message, member: Member):
	'Clears the most recent infraction for a member'
	if not member:
		return await message.send('Please use `!clearrecentinfraction @member`')
	await db.clear_recent_infraction(member.id)

	await message.add_reaction(confirmed_emoji)
