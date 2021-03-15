import forumsweats.discordbot as discordbot
from ..betterbot import Member
import discord
from forumsweats import db

name = 'duelstreak'
aliases = ('duel-streak', 'duelwinstreak', 'duel-winstreak', 'duelwin-streak', 'duel-win-streak')
args = '[member]'


async def run(message, member: Member = None):
	'Tells you your current duel winstreak in #general'
	if not member:
		member = message.author
	winstreak = await db.fetch_duel_winstreak(member.id)
	if member.id == message.author.id:
		winstreak_message = f'Your duel winstreak is **{winstreak}**'
	else:
		winstreak_message = f'<@{member.id}> has a duel winstreak of **{winstreak}**'
	embed = discord.Embed(
		description=winstreak_message
	)
	await message.channel.send(embed=embed)
