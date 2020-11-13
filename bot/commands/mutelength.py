from ..betterbot import Member
from ..discordbot import unmute_user
from utils import seconds_to_string
import discord
import time
import db

name = 'mutelength'
aliases = ['mutetime']
channels = ['bot-commands', 'gulag']


async def run(message, member: Member = None):
	if not member:
		member = message.author

	mute_remaining = int((await db.get_mute_end(member.id)) - time.time())

	if mute_remaining < 0:
		await unmute_user(member.id, True, False)
		if member.id == message.author.id:
			await message.send(embed=discord.Embed(
				description="You aren't muted."
			))
		else:
			await message.send(embed=discord.Embed(
				description=f"<@{member.id}> isn't muted."
			))
	else:
		mute_str = seconds_to_string(mute_remaining)
		if member.id == message.author.id:
			await message.send(embed=discord.Embed(
				description=f'You are muted for {mute_str}'
			))
		else:
			await message.send(embed=discord.Embed(
				description=f'<@{member.id}> is muted for {mute_str}'
			))
