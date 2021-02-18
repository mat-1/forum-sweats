from forumsweats.betterbot import Member
from forumsweats import confirmgui
from .sub import is_subbed
import discord
from forumsweats import db

name = 'unsub'
aliases = ['unsimp', 'bobuxunsub', 'unbobuxsub', 'unsubscribe', 'bobuxunsubscribe', 'bobuxunsimp']


async def unsubscribe(user, unsubbing_to):
	user_id = user.id if hasattr(user, 'id') else int(user)
	unsubbing_to_id = unsubbing_to.id if hasattr(unsubbing_to, 'id') else int(unsubbing_to)
	await db.bobux_unsubscribe_to(user_id, unsubbing_to_id)


async def run(message, member: Member = None):
	if not member:
		return await message.channel.send('Invalid member.')

	if not await is_subbed(message.author, member):
		return await message.channel.send('You\'re not subbed to this member.')

	verify_message = await message.channel.send(embed=discord.Embed(
		description=f'Are you sure you want to unsub from {member.mention}? You will not get a refund.'
	))
	confirmed = await confirmgui.make_confirmation_gui(message.client, verify_message, message.author)

	edited_content = None

	if confirmed:
		if await is_subbed(message.author, member):
			await unsubscribe(message.author, member)
			edited_content = f'Unsubbed from {member.mention}.'
		else:
			edited_content = f'You\'re not subbed to {member.mention}.'
	else:
		edited_content = f'Cancelled unsub from {member.mention}!'

	await verify_message.edit(embed=discord.Embed(
		description=edited_content
	))
