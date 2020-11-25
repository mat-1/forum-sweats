from bot.betterbot import Member
from bot import confirmgui
import discord
import db

name = 'unsub'
aliases = ['unsimp', 'bobuxunsub', 'unbobuxsub', 'unsubscribe', 'bobuxunsubscribe', 'bobuxunsimp']


async def unsubscribe(user, unsubbing_to):
	await db.bobux_unsubscribe_to(user.id, unsubbing_to.id)


async def run(message, member: Member = None):
	if not member:
		return await message.channel.send('Invalid member.')

	verify_message = await message.channel.send(embed=discord.Embed(
		description=f'Are you sure you want to unsub from {member.mention}? You will not get a refund.'
	))
	confirmed = await confirmgui.make_confirmation_gui(message.client, verify_message, message.author)

	if confirmed:
		await unsubscribe(message.author, member)
		await verify_message.edit(embed=discord.Embed(
			description=f'Unsubbed from {member.mention}.'
		))
	else:
		await verify_message.edit(embed=discord.Embed(
			description=f'Cancelled unsub from {member.mention}!'
		))
