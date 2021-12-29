import forumsweats.discordbot as discordbot
from ..commandparser import Member
import discord
from forumsweats import db

name = 'socialcredit'
args = '[member]'
aliases = ('sc',)


async def run(message, member: Member = None):
	if not member:
		member = message.author
	social_credit = await db.get_base_social_credit(member.id) + 1000
	if social_credit >= 1050:
		grade = 'AAA'
	elif social_credit >= 1030:
		grade = 'AA'
	elif social_credit >= 1001:
		grade = 'A+'
	elif social_credit == 1000:
		grade = 'A'
	elif social_credit >= 960:
		grade = 'A-'
	elif social_credit >= 850:
		grade = 'B'
	elif social_credit >= 600:
		grade = 'C'
	else:
		grade = 'D'

	if member.id == message.author.id:
		social_credit_message = f'You have **{social_credit}** social credit. That means you have a grade of **{grade}**.'
	else:
		social_credit_message = f'<@{member.id}> has **{social_credit}** social credit. That means they have a grade of **{grade}**.'
	embed = discord.Embed(
		description=social_credit_message
	)
	await message.channel.send(embed=embed)
