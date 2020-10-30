from ..betterbot import Member
import bot.discordbot as discordbot
import discord
import db

name = 'bobuxleaderboard'
aliases = ['leaderboard', 'lb', 'bobuxlb', 'leaderboardbobux', 'lbbobux', 'blb']


async def run(message):
	print('doing bobux leaderboard')
	leaderboard_raw = await db.get_bobux_leaderboard()
	print('doing bobux leaderboard2')
	leaderboard_strings = []
	for position_0, member in enumerate(leaderboard_raw):
		print('doing bobux leaderboard3')
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
