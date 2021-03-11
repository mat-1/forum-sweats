import forumsweats.discordbot as discordbot
from ..betterbot import Member
import discord
from forumsweats import db

name = 'activitybobux'
args = '[member]'


async def run(message, member: Member = None):
	'''
Tells you how much activity bobux you have
Activity bobux is like bobux but cannot be used for anything, and you only get it from sending messages
	'''
	if not member:
		member = message.author
	bobux = await db.get_activity_bobux(member.id)
	if member.id == message.author.id:
		bobux_message = f'You have **{bobux}** activity bobux'
	else:
		bobux_message = f'<@{member.id}> has **{bobux}** activity bobux'
	embed = discord.Embed(
		description=bobux_message
	)
	await message.channel.send(embed=embed)
