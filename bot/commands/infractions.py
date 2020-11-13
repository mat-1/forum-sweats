from utils import confirmed_emoji
from ..discordbot import has_role
from ..betterbot import Member
import discord
import config
import db

name = 'infractions'
bot_channel = False


async def run(message, member: Member = None):
	'Checks the infractions that a user has (mutes, warns, bans, etc)'

	if not member:
		member = message.author

	is_checking_self = message.author.id == member.id

	if (
		not is_checking_self
		and not has_role(message.author.id, 'helper')
		and not has_role(message.author.id, 'trialhelper')
	):
		return

	infractions = await db.get_infractions(member.id)

	embed_title = 'Your infractions' if is_checking_self else f'{member}\'s infractions'

	embed = discord.Embed(
		title=embed_title
	)
	for infraction in infractions[-30:]:
		value = infraction.get('reason') or '<no reason>'
		name = infraction['type']
		infraction_partial_id = infraction['_id'][:8]
		if 'date' in infraction:
			date_pretty = infraction['date'].strftime('%m/%d/%Y')
			name += f' ({date_pretty} {infraction_partial_id})'
		else:
			name += f' ({infraction_partial_id})'
		if len(value) > 1000:
			value = value[:1000] + '...'
		embed.add_field(
			name=name,
			value=value,
			inline=False
		)

	if len(infractions) == 0:
		embed.description = 'No infractions'

	if is_checking_self:
		await message.author.send(embed=embed)
		await message.add_reaction(confirmed_emoji)
	else:
		await message.send(embed=embed)
