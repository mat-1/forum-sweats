from distutils.command.config import config

import discord
from forumsweats.commandparser import Member
import config

# BAN MEE6
async def welcome_user(member):
    guild = member.guild
    channel = guild.get_channel(config.channels.get('welcome'))
    avatar = member.avatar or member.default_avatar
    name = member.name

    if channel is None:
        return

    embed = discord.Embed(title=f'{name} just joined Forum Sweats!', description=f'Member #{guild.member_count}')
    embed.set_thumbnail(url=avatar)

    
    await channel.send(f'Welcome to Forum Sweats, {member.mention}!', embed=embed)
    
