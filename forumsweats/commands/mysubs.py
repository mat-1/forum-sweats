from utils import seconds_to_string
from forumsweats.betterbot import Member
from datetime import datetime
from .sub import tiers
import discord
from forumsweats import db

name = 'mysubs'
aliases = ['mysimps', 'mysubscribers', 'simps']


async def run(message, member: Member = None):
	if not member:
		member = message.author
	subs = await db.bobux_get_all_subscriptions(member.id)
	display_message = []
	total_earning = 0

	for sub in subs:
		sender = sub['sender']
		tier = sub['tier']
		tier_upper = tier.upper()
		next_payment_delta = sub['next_payment'] - datetime.utcnow()
		next_payment_seconds = next_payment_delta.total_seconds()
		next_payment_display = seconds_to_string(next_payment_seconds)
		display_message.append(
			f'<@{sender}> - **{tier_upper}** (next payment in {next_payment_display})'
		)
		total_earning += tiers[tier]

	if member == message.author:
		title = 'Your simps'
	else:
		title = f'{member}\'s simps'

	title += f' ({total_earning} bobux earnt per week)'

	await message.channel.send(embed=discord.Embed(
		title=title,
		description='\n'.join(display_message) or '*no simps*'
	))
