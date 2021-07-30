from ..commandparser import Member
from ..discordbot import has_role
from utils import confirmed_emoji
from datetime import timedelta
from forumsweats import db
import discord

name = 'infractions'
channels = None
args = '<member>'

INFRACTION_TYPE_EMOJIS = {
	'mute': '🔇',
	'warn': '⚠️',
	'moot': '<:troll:798727241001467904>',
}

async def run(message, member: Member = None):
	'Tells you the times you have been muted and why.'


	if not member:
		member = message.author

	is_checking_self = message.author.id == member.id

	if (
		not is_checking_self
		and not has_role(message.author.id, 'helper')
		and not has_role(message.author.id, 'trialhelper')
	):
		return

	infractions = await db.get_all_infractions(member.id)

	embed_title = 'Your infractions' if is_checking_self else f'{member}\'s infractions'

	embed = discord.Embed(
		title=embed_title
	)

	total_mutes = 0
	total_mutes_past_month = 0

	for infraction in infractions:
		name = infraction['type']
		if name == 'mute':
			total_mutes += 1
		if 'date' in infraction:
			if discord.utils.utcnow() - timedelta(days=30) > infraction['date']:
				continue
			if name == 'mute':
				total_mutes_past_month += 1
	
	for infraction in infractions[-30:]:
		value = infraction.get('reason') or '<no reason>'
		name = infraction['type']

		# add the emoji for the infraction type before the name
		if name in INFRACTION_TYPE_EMOJIS:
			name = f'{INFRACTION_TYPE_EMOJIS[name]} {name}'

		infraction_partial_id = infraction['_id'][:8]

		if 'date' in infraction:
			if discord.utils.utcnow() - infraction['date'] > timedelta(days=30):
				continue

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
	
	if total_mutes > total_mutes_past_month:
		embed.set_footer(
			text=f'{total_mutes} total infractions, {total_mutes_past_month} from past month'
		)
	else:
		embed.set_footer(
			text=f'{total_mutes} total infractions'
		)

	if len(infractions) == 0:
		embed.description = 'No infractions'

	if is_checking_self:
		await message.author.send(embed=embed)
		await message.add_reaction(confirmed_emoji)
	else:
		await message.send(embed=embed)
