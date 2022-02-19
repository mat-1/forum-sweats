import forumsweats.discordbot as discordbot
from ..commandparser import Member
import discord
from forumsweats import db
from forumsweats import confirmgui

name = 'transferaccount'
channels = None
roles = ('admin',)
args = '<oldmember> <newmember>'

async def run(message, oldmember: Member = None, newmember: Member = None):
	'Transfers the Forum Sweats data from one Discord account to another.'
	if not oldmember:
		return await message.reply(f'Invalid old member. Usage: `{message.prefix}transferaccount <oldmember> <newmember>`')
	if not newmember:
		return await message.reply(f'Invalid new member. Usage: `{message.prefix}transferaccount <oldmember> <newmember>`')

	verify_message = await message.reply(f'Are you really sure you want to transfer the Forum Sweats data from <@{oldmember.id}> ({oldmember.id}) to <@{newmember.id}> ({newmember.id})? Don\'t do this unless they are switching Discord accounts.')
	confirmed = await confirmgui.make_confirmation_gui(message.client, verify_message, message.author)
	if not confirmed:
		return
	
	transferring_message = await message.reply('Ok, transferring data...')

	# ok, transfer everything
	# bobux
	old_bobux = await db.get_bobux(oldmember.id)
	await db.change_bobux(newmember.id, old_bobux)
	await db.change_bobux(oldmember.id, -old_bobux)

	# activity bobux
	old_activity_bobux = await db.get_activity_bobux(oldmember.id)
	await db.change_activity_bobux(newmember.id, old_activity_bobux)
	await db.change_activity_bobux(oldmember.id, -old_activity_bobux)

	# infractions
	await db.transfer_infractions(oldmember.id, newmember.id)

	# social credit
	old_social_credit = await db.get_base_social_credit(oldmember.id)
	await db.change_social_credit(newmember.id, old_social_credit)
	await db.change_social_credit(oldmember.id, -old_social_credit)

	# subs
	await db.transfer_bobux_subscriptions(oldmember.id, newmember.id)

	# shop items
	bought_shop_items = await db.get_bought_shop_items(oldmember.id)
	for item in bought_shop_items:
		await db.get_shop_item(newmember.id, item)
		await db.lose_shop_item(oldmember.id, item)


	await discordbot.check_bobux_roles(oldmember.id)
	await discordbot.check_bobux_roles(newmember.id)

	await transferring_message.edit(content='Done!')

async def on_no_perms(message):
	await message.reply(f'You do not have permission to use this command, did you mean {message.prefix}sendbobux?.')
