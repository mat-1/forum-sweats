import forumsweats.discordbot as discordbot
from ..betterbot import Member
import discord
from forumsweats import db

name = 'bobux'
args = '<member>'


async def run(message, member: Member = None):
	'Tells you how much bobux you have'
	if not member:
		member = message.author
	bobux = await db.get_bobux(member.id)
	if member.id == message.author.id:
		bobux_message = f'You have **{bobux}** bobux'
	else:
		bobux_message = f'<@{member.id}> has **{bobux}** bobux'
	embed = discord.Embed(
		description=bobux_message
	)
	await message.channel.send(embed=embed)
	await discordbot.check_bobux_roles(member.id, bobux)
