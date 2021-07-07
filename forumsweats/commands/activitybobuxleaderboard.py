from ..commandparser import Member
import forumsweats.discordbot as discordbot
import discord
from forumsweats import db

name = 'activityleaderboard'
# activity leaderboard, activity bobux leaderboard, etc
aliases = ('al', 'abl', 'alb', 'ablb', 'activitybobuxleaderboard', 'activitylb')

async def run(message, page: int=1):
	'Shows who has the most activity'
	leaderboard_raw = await db.get_activity_bobux_leaderboard(page=page)
	leaderboard_strings = []
	for position_0, member in enumerate(leaderboard_raw):
		position = position_0 + 1
		member_id = member['discord']
		bobux = member['bobux']
		leaderboard_strings.append(f'{position}) <@{member_id}> (**{bobux}** activity bobux)')
	embed = discord.Embed(
		title='Activity Leaderboard',
		description='\n'.join(leaderboard_strings)
	)
	await message.channel.send(embed=embed)
