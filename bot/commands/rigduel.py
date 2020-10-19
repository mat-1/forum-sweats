from ..betterbot import Member

name = 'rigduel'
aliases = ['rigduels']
bot_channel = False

rigged_duel_users = set()


async def run(message, member: Member = None):
	global rigged_duel_users
	if message.author.id != 461340349680582667: return  # only works for antisynth anti for staff
	rigged_duel_users.add(member.id if member else message.author.id)
	await message.delete()
