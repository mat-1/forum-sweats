from forumsweats.commands.pets import get_active_pet
from .rigduel import rigged_duel_users
from .givepet import give_unique_pet
from utils import seconds_to_string
from ..discordbot import mute_user
from ..betterbot import Member
from forumsweats import db
from typing import Union
import asyncio
import discord
import config
import random
import time


name = 'duel'
channels = ('general', 'bot-commands', 'gulag', 'staff-duel')
args = '<member>'

duel_statuses = {}
active_duelers = set()


async def duel_wait_for(client, channel, opponent_1, opponent_2):
	global duel_statuses

	def duel_check(message):
		print(message.content.strip())
		return (
			message.author.id in {opponent_1.id, opponent_2.id}
			and message.content in {'🔫', ':gun:'}
		)
	try:

		message = await client.wait_for('message', check=duel_check, timeout=60)
	except asyncio.TimeoutError:
		if opponent_1.id in active_duelers:
			active_duelers.remove(opponent_1.id)
		if opponent_2.id in active_duelers:
			active_duelers.remove(opponent_2.id)
		return
	duel_id = get_duel_id(opponent_1, opponent_2)
	duel_at_zero = duel_statuses[duel_id]['zero']
	duel_statuses[duel_id]['ended'] = True
	rigged = False

	opponent_1_active_pet = await get_active_pet(opponent_1.id)
	opponent_2_active_pet = await get_active_pet(opponent_2.id)

	# "Gladiator" gladiator pet ability
	if opponent_1_active_pet and opponent_1_active_pet.id == 'gladiator':
		if random.random() >= .9:
			rigged_duel_users.add(opponent_1.id)
	if opponent_2_active_pet and opponent_2_active_pet.id == 'gladiator':
		if random.random() >= .9:
			rigged_duel_users.add(opponent_2.id)

	if duel_at_zero:
		duel_winner: Union[Member] = message.author
		duel_loser = opponent_1 if duel_winner == opponent_2 else opponent_2
		if duel_loser.id in rigged_duel_users:
			rigged_duel_users.remove(duel_loser.id)
			duel_winner_tmp = duel_winner
			duel_winner = duel_loser
			duel_loser = duel_winner_tmp
			rigged = True
		await channel.send(f'<@{duel_winner.id}> won the duel!')
	else:
		duel_winner = opponent_1 if message.author == opponent_2 else opponent_2
		duel_loser = opponent_1 if duel_winner == opponent_2 else opponent_2
		if duel_loser.id in rigged_duel_users:
			rigged_duel_users.remove(duel_loser.id)
			duel_winner_tmp = duel_winner
			duel_winner = duel_loser
			duel_loser = duel_winner_tmp
			rigged = True

		await channel.send(f'<@{duel_winner.id}> won the duel because <@{duel_loser.id}> shot too early')
	if channel.id == 750147192383078400:  # quaglet channel
		mute_length = 0
	elif channel.id == config.channels['general']:  # general
		mute_length: int = 60 * 15

		winner_active_pet = await get_active_pet(duel_winner.id)

		# "Harder blows" gladiator pet ability
		if winner_active_pet and winner_active_pet.id == 'gladiator':
			mute_length = int(mute_length * 1.5)

		mute_length_string = seconds_to_string(mute_length)

		try: await duel_loser.send(f'You were muted for {mute_length_string} because you lost a duel in general')
		except: pass

		# increase the winstreak of the winner
		last_dueled_member_id = await db.fetch_last_dueled_member(duel_winner.id)

		await db.set_last_dueled_member(duel_loser.id, duel_winner.id)
		await db.set_last_dueled_member(duel_winner.id, duel_loser.id)
		# reset the winstreak of the loser
		await db.reset_duel_winstreak(duel_loser.id)

		# make sure the last person the winner dueled was someone different
		if last_dueled_member_id != duel_loser.id:
			await db.increase_duel_winstreak(duel_winner.id)

			winstreak = await db.fetch_duel_winstreak(duel_winner.id)
			if winstreak == 1:
				await db.change_bobux(duel_winner.id, 20)
			elif winstreak == 2:
				await db.change_bobux(duel_winner.id, 50)
			elif winstreak == 3:
				await db.change_bobux(duel_winner.id, 100)
			elif winstreak >= 4:
				await db.change_bobux(duel_winner.id, 200)
				await give_unique_pet(duel_winner, 'gladiator')

	elif channel.id == config.channels.get('gulag'):  # gulag
		mute_end = await db.get_mute_end(duel_loser.id)
		mute_remaining = int(mute_end - time.time())
		mute_length = mute_remaining + 60 * 5
	else:
		mute_length = 60 * 1
		try:
			await duel_loser.send('You were muted for one minute because you lost a duel')
		except discord.errors.Forbidden:
			pass
		except AttributeError:
			pass
	try:
		del duel_statuses[duel_id]
	except KeyError:
		pass
	if opponent_1.id in active_duelers:
		active_duelers.remove(opponent_1.id)
	if opponent_2.id in active_duelers:
		active_duelers.remove(opponent_2.id)

	if mute_length > 0:
		await mute_user(
			duel_loser,
			mute_length,
			channel.guild.id if channel.guild else None
		)

	if not rigged and duel_loser.id == message.guild.me.id and channel.id == config.channels.get('general'):
		print('won in general!', duel_winner.id)
		# if you win against forum sweats in general, you get 50 bobux
		await db.change_bobux(duel_winner.id, 50)
		print('epic gaming moment')


def get_duel_id(opponent_1, opponent_2):
	if opponent_1.id > opponent_2.id:
		return f'{opponent_1.id} {opponent_2.id}'
	else:
		return f'{opponent_2.id} {opponent_1.id}'



async def run(message, opponent: Member):
	'Duel another member by waiting for a countdown and sending the 🔫 emoji. '\
	'You will get muted for 15 minutes (or more) if you lose a duel in <#719579620931797002>'
	global duel_statuses

	if not opponent:
		return await message.channel.send('You must choose an opponent (example: !duel quaglet)')
	if opponent.id == message.author.id:
		return await message.channel.send("You can't duel yourself")

	mute_end = await db.get_mute_end(message.author.id)
	if (mute_end and mute_end > time.time()) and message.channel.id != config.channels['gulag']:
		return await message.channel.send("You can't use this command while muted")
	mute_end = await db.get_mute_end(opponent.id)
	if (mute_end and mute_end > time.time()) and message.channel.id != config.channels['gulag']:
		return await message.channel.send('Your opponent is muted')
	if message.author.id in active_duelers:
		return await message.channel.send("You're already in a duel")
	if opponent.id in active_duelers:
		return await message.channel.send("That person is already in a duel")
	active_duelers.add(message.author.id)

	duel_id = get_duel_id(message.author, opponent)
	if duel_id in duel_statuses:
		return await message.channel.send('You already sent a duel request to this person')
	duel_statuses[duel_id] = {
		'zero': False,
		'ended': False
	}
	if message.channel.id == config.channels['general']:
		duel_invite_text = (
			f'<@{opponent.id}>, react to this message with :gun: to duel <@{message.author.id}>. '
			'The loser will get muted for 15 minutes'
		)
	else:
		duel_invite_text = f'<@{opponent.id}>, react to this message with :gun: to duel <@{message.author.id}>'
	duel_invite_message = await message.channel.send(duel_invite_text)
	await duel_invite_message.add_reaction('🔫')
	try:
		if opponent.id != message.guild.me.id:
			reaction, user = await message.client.wait_for(
				'reaction_add',
				check=lambda reaction, user: (
					user.id == opponent.id and reaction.emoji == '🔫' and reaction.message.id == duel_invite_message.id
				),
				timeout=60
			)
	except asyncio.TimeoutError:
		del duel_statuses[duel_id]
		if message.author.id in active_duelers:
			active_duelers.remove(message.author.id)

		return await duel_invite_message.edit(
			content='The opponent didn\'t react to this message, so the duel has been cancelled.'
		)

	if opponent.id in active_duelers:
		return

	active_duelers.add(opponent.id)

	asyncio.ensure_future(duel_wait_for(message.client, message.channel, message.author, opponent))

	is_testing = message.author.id == 1

	await message.channel.send('Duel starting in 10 seconds... First person to type :gun: once the countdown ends, wins.')

	if not is_testing: await asyncio.sleep(5)

	while (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('5')
			if not is_testing: await asyncio.sleep(1)
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('4')
			if not is_testing: await asyncio.sleep(1)
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('3')
			if not is_testing: await asyncio.sleep(1)
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('2')
			if not is_testing: await asyncio.sleep(1)
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('1')
			if not is_testing: await asyncio.sleep(1)
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('Shoot')
			is_bot_shooting = duel_id in duel_statuses and not duel_statuses[duel_id]['ended']
			if duel_id in duel_statuses and not duel_statuses[duel_id]['ended']:
				duel_statuses[duel_id]['zero'] = True
				duel_statuses[duel_id]['ended'] = True
			if is_testing:  # if its a unit test give it a free extra second
				await asyncio.sleep(1)
			if is_bot_shooting:
				if opponent.id == message.guild.me.id:
					await message.channel.send(':gun:')
		else:
			if duel_id in duel_statuses:
				duel_statuses[duel_id]['zero'] = True
		await asyncio.sleep(1)
	if message.author.id in active_duelers:
		active_duelers.remove(message.author.id)
	if opponent.id in active_duelers:
		active_duelers.remove(opponent.id)
