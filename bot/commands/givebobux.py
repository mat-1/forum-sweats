import bot.discordbot as discordbot
from ..discordbot import has_role
from ..betterbot import Member
import discord
import db

name = 'givebobux'
bot_channel = False


async def run(message, member: Member = None, amount: int = 0):
	if not has_role(message.author.id, 717904501692170260, 'admin'): return
	if not member:
		return await message.channel.send('Invalid member')
	if not amount:
		return await message.channel.send('Invalid amount')
	await db.change_bobux(member.id, amount)
	reciever_bobux = await db.get_bobux(member.id)
	await message.channel.send(
		embed=discord.Embed(
			description=f'Ok, <@{member.id} now has **{reciever_bobux}** bobux.'
		)
	)
	await discordbot.check_bobux_roles(member.id, reciever_bobux)
