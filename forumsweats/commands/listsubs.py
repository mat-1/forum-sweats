from forumsweats.commandparser import Member
from utils import seconds_to_string
from forumsweats import db
from .sub import tiers
import discord

name = 'listsubs'
args = '[member]'

# hmm yes these aliases are definitely going to get used
aliases = [
	'subs', 'bobuxsubs', 'listbobuxsubs', 'listbobuxsub', 'subbed', 'sublist', 'subscribelist', 'subscriptionlist',
	'listsubscriptions'
]


async def run(message, member: Member = None):
	'Lists who you\'re subbed to.'
	if not member:
		# Default to the message author if the member is omitted
		member = message.author

	subs = await db.bobux_get_subscriptions(member.id)
	display_message = []
	total_spending = 0
	for sub in subs:
		receiver = sub['id']
		tier = sub['tier']
		tier_upper = tier.upper()
		next_payment_delta = sub['next_payment'] - discord.utils.utcnow()
		next_payment_seconds = next_payment_delta.total_seconds()
		next_payment_display = seconds_to_string(next_payment_seconds)
		display_message.append(
			f'<@{receiver}> - **{tier_upper}** (next payment in {next_payment_display})'
		)
		total_spending += tiers[tier]

	if member == message.author:
		title = 'Your subs'
	else:
		title = f'{member}\'s subs'

	title += f' ({total_spending:,} bobux spent per week)'

	await message.channel.send(embed=discord.Embed(
		title=title,
		description='\n'.join(display_message) or 'no subs'
	))
