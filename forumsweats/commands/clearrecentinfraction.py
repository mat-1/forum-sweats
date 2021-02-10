from utils import confirmed_emoji
from ..discordbot import has_role
from ..betterbot import Member
from forumsweats import db

name = 'clearrecentinfraction'
aliases = ['clearnewinfraction']
channels = None


async def run(message, member: Member):
	if (
		not has_role(message.author.id, 'helper')
		and not has_role(message.author.id, 'trialhelper')
	):
		return

	if not member:
		return await message.send('Please use `!clearrecentinfraction @member`')
	await db.clear_recent_infraction(member.id)

	await message.add_reaction(confirmed_emoji)
