from ..discordbot import has_role
import discord
import db

name = 'clearinfraction'
aliases = ['removeinfraction']
bot_channel = False


async def run(message, infraction_id: str):
	'Checks the infractions that a user has (mutes, warns, bans, etc)'

	if (
		not has_role(message.author.id, 717904501692170260, 'helper')
		and not has_role(message.author.id, 717904501692170260, 'trialhelper')
	):
		return

	if len(infraction_id) != 8:
		return await message.send('Incorrect command usage. Example: `!clearinfraction abcdef69`')

	data = await db.clear_infraction_by_partial_id(infraction_id)
	if not data:
		return await message.send('Infraction not found')
	else:
		user_id = data['user']
		return await message.send(
			embed=discord.Embed(description=f'Cleared an infraction from <@{user_id}>')
		)
