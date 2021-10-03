import forumsweats.discordbot as discordbot
from ..commandparser import Member
import discord
from forumsweats import db

name = 'bobux'
args = '[member]'
aliases = ('kromer',)


async def run(message, member: Member = None):
	'Tells you how much bobux you have'
	if not member:
		member = message.author
	bobux = await db.get_bobux(member.id)

	currency_name = 'kromer' if message.command_name == 'kromer' else 'bobux'

	if member.id == message.author.id:
		bobux_message = f'You have **{bobux:,}** {currency_name}'
	else:
		bobux_message = f'<@{member.id}> has **{bobux:,}** {currency_name}'
	embed = discord.Embed(
		description=bobux_message
	)
	await message.channel.send(embed=embed)
	await discordbot.check_bobux_roles(member.id, bobux)
