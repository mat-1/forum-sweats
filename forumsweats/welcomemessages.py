import discord
from forumsweats.commandparser import Member
import config

async def welcome_user(member):
	channel = member.guild.get_channel(config.channels.get('welcome'))
	rules_channel_id = config.channels.get('rules')
	avatar = member.avatar or member.default_avatar

	if channel is None:
		return

	embed = discord.Embed(
		title=f'{member} just joined Forum Sweats.',
		description=f'Please make sure to read the rules at <#{rules_channel_id}>.',
		color=0xA40985
	)
	embed.set_footer(text=f'Member #{member.guild.member_count}')
	embed.set_thumbnail(url=avatar)

	
	await channel.send(f'Welcome to Forum Sweats, {member.mention}!', embed=embed)
