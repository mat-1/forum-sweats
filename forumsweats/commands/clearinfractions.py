from ..betterbot import Member
from ..discordbot import has_role
from datetime import datetime
from forumsweats import db

name = 'clearinfractions'
channels = None


async def run(message, member: Member, date_string: str = None):
	'Checks the infractions that a user has (mutes, warns, bans, etc)'

	if (
		not has_role(message.author.id, 'helper')
		and not has_role(message.author.id, 'trialhelper')
	):
		return

	if not member or not date_string:
		return await message.send('Please use `!clearinfractions @member date`')
	# month, day, year = date.split('/')
	if date_string == 'today':
		date = datetime.utcnow()
	else:
		try:
			date = datetime.strptime(date_string.strip(), '%m/%d/%Y')
		except ValueError:
			return await message.send('Invalid date (use format mm/dd/yyyy)')
	cleared = await db.clear_infractions(member.id, date)

	if cleared > 1:
		return await message.send(f'Cleared {cleared} infractions from that date.')
	if cleared == 1:
		return await message.send('Cleared 1 infraction from that date.')
	else:
		return await message.send('No infractions found from that date.')
