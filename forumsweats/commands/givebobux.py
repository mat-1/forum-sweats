import forumsweats.discordbot as discordbot
from ..betterbot import Member
import discord
from forumsweats import db

name = 'givebobux'
channels = None
roles = ('admin',)
args = '<member> <amount>'

async def run(message, member: Member = None, amount: int = 0):
	'Gives bobux to a user. Don\'t abuse this!'
	if not member:
		return await message.channel.send('Invalid member')
	if not amount:
		return await message.channel.send('Invalid amount')
	await db.change_bobux(member.id, amount)
	reciever_bobux = await db.get_bobux(member.id)
	await message.channel.send(
		embed=discord.Embed(
			description=f'Ok, <@{member.id}> now has **{reciever_bobux}** bobux.'
		)
	)
	await discordbot.check_bobux_roles(member.id, reciever_bobux)
