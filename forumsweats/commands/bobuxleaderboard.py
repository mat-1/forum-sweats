from ..betterbot import Member
import forumsweats.discordbot as discordbot
import discord
from forumsweats import db

name = 'bobuxleaderboard'
aliases = ('leaderboard', 'lb', 'bobuxlb', 'leaderboardbobux', 'lbbobux', 'blb')


async def run(message):
	leaderboard_raw = await db.get_bobux_leaderboard()
	leaderboard_strings = []
	for position_0, member in enumerate(leaderboard_raw):
		position = position_0 + 1
		member_id = member['discord']
		bobux = member['bobux']
		leaderboard_strings.append(f'{position}) <@{member_id}> (**{bobux}** bobux)')
	print(leaderboard_strings)
	embed = discord.Embed(
		title='Bobux Leaderboard',
		description='\n'.join(leaderboard_strings)
	)
	await message.channel.send(embed=embed)
