import forumsweats.discordbot as discordbot
from ..commandparser import Member
import discord
from forumsweats import db

name = 'givebobux'
channels = None
roles = ('admin',)
args = '<member> <amount>'

async def run(message, member: Member = None, amount: int = 0):
	'Gives bobux to a user. Don\'t abuse this!'
	if not member:
		return await message.reply('Invalid member')
	if not amount:
		return await message.reply('Invalid amount')
	await db.change_bobux(member.id, amount)
	reciever_bobux = await db.get_bobux(member.id)
	await message.reply(
		embed=discord.Embed(
			description=f'Ok, <@{member.id}> now has **{reciever_bobux}** bobux.'
		)
	)
	await discordbot.check_bobux_roles(member.id, reciever_bobux)

async def on_no_perms(message):
	await message.reply(f'You do not have permission to use this command, did you mean {message.prefix}sendbobux?.')
