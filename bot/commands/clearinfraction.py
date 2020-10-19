from ..discordbot import has_role
import discord
import db

name = 'clearinfraction'
aliases = ['removeinfraction']
bot_channel = False


async def run(message, infraction_ids: str):
	'Checks the infractions that a user has (mutes, warns, bans, etc)'

	if (
		not has_role(message.author.id, 717904501692170260, 'helper')
		and not has_role(message.author.id, 717904501692170260, 'trialhelper')
	):
		return

	infraction_ids = infraction_ids.split(' ')

	for infraction_id in infraction_ids:
		if len(infraction_id) != 8:
			return await message.send('Incorrect command usage. Example: `!clearinfraction abcdef69`')

	cleared_count = 0
	cleared_users = set()

	for infraction_id in infraction_ids:
		data = await db.clear_infraction_by_partial_id(infraction_id)
		if not data:
			return await message.send(f'Infraction {infraction_id} not found')
		else:
			cleared_count += 1
			cleared_users.add(data['user'])

	if cleared_count == 0:
		cleared_message = 'Cleared no infractions'
	elif cleared_count == 1:
		cleared_message = f'Cleared an infraction from <@{cleared_users[0]}>'
	elif cleared_count > 1 and len(cleared_users) == 1:
		cleared_message = f'Cleared {cleared_count} infractions from <@{cleared_users[0]}>'
	elif cleared_count > 1 and len(cleared_users) > 1:
		cleared_message = f'Cleared {cleared_count} infractions from {len(cleared_users[0])} users'
	else:
		cleared_message = 'Cleared infractions'
	return await message.send(
		embed=discord.Embed(description=cleared_message)
	)
