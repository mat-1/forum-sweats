from forumsweats.commands.infractions import INFRACTION_TYPE_EMOJIS
from datetime import datetime, timedelta
from utils import confirmed_emoji
from ..commandparser import Member
from forumsweats import db
import discord

name = 'mutes'
channels = None
args = '<member>'
roles = ('helper', 'trialhelper')

async def run(message, member: Member = None):
	'See who you (or another staff member) has muted.'

	if not member:
		member = message.author

	infractions = await db.get_all_infractions_by(member.id)

	is_checking_self = member.id == message.author.id

	embed_title = 'Your mutes' if is_checking_self else f'{member}\'s mutes'

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
		value = f'<@{infraction["user"]}> - ' + (infraction.get('reason') or '<no reason>')
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
			text=f'{total_mutes} total muted, {total_mutes_past_month} from past month'
		)
	else:
		embed.set_footer(
			text=f'{total_mutes} total muted'
		)

	if len(infractions) == 0:
		embed.description = 'No mutes'

	if is_checking_self:
		await message.author.send(embed=embed)
		await message.add_reaction(confirmed_emoji)
	else:
		await message.send(embed=embed)
