from .rigduel import rigged_duel_users
from ..discordbot import mute_user
from ..betterbot import Member
import asyncio
import random
import time
import db

duel_statuses = {}
active_duelers = set()


async def duel_wait_for(client, channel, opponent_1, opponent_2):
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
	if duel_at_zero:
		duel_winner = message.author
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
		print(1)
	if channel.id == 750147192383078400:  # quaglet channel
		mute_length = 0
	elif channel.id == 719579620931797002:  # general
		mute_length = 60 * 60
		try:
			await duel_loser.send("You were muted for one hour because you lost a duel in general")
		except:
			pass
		print(2)
	elif channel.id == 720073985412562975:  # gulag
		mute_end = await db.get_mute_end(duel_loser.id)
		mute_remaining = mute_end - time.time()
		mute_length = mute_remaining + 60 * 5
	else:
		mute_length = 60 * 1
		try:
			await duel_loser.send("You were muted for one minute because you lost a duel")
		except:
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

	if not rigged and duel_loser.id == 719348452491919401 and channel.id == 719579620931797002:
		# if you win against forum sweats in general, you get 50 bobux
		await db.change_bobux(duel_winner.id, 50)


def get_duel_id(opponent_1, opponent_2):
	if opponent_1.id > opponent_2.id:
		return f'{opponent_1.id} {opponent_2.id}'
	else:
		return f'{opponent_2.id} {opponent_1.id}'


name = 'duel'
bot_channel = False


async def run(message, opponent: Member):
	if message.channel.id not in {
		719579620931797002,  # general
		718076311150788649,  # bot-commands
		720073985412562975,  # gulag
		750147192383078400,  # quaglet channel
	}: return

	if not opponent:
		return await message.channel.send('You must choose an opponent (example: !duel quaglet)')
	if opponent.id == message.author.id:
		return await message.channel.send("You can't duel yourself")

	mute_end = await db.get_mute_end(message.author.id)
	if (mute_end and mute_end > time.time()) and not message.channel.id == 720073985412562975:
		return await message.channel.send("You can't use this command while muted")
	mute_end = await db.get_mute_end(opponent.id)
	if (mute_end and mute_end > time.time()) and not message.channel.id == 720073985412562975:
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
	if message.channel.id == 719579620931797002:
		duel_invite_text = f'<@{opponent.id}>, react to this message with :gun: to duel <@{message.author.id}>. The loser will get muted for one hour'
	else:
		duel_invite_text = f'<@{opponent.id}>, react to this message with :gun: to duel <@{message.author.id}>'
	duel_invite_message = await message.channel.send(duel_invite_text)
	await duel_invite_message.add_reaction('🔫')
	try:
		if opponent.id != 719348452491919401:
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

		return await duel_invite_message.edit(content="The opponent didn't react to this message, so the duel has been cancelled.")

	if opponent.id in active_duelers:
		return
	active_duelers.add(opponent.id)

	if message.channel.id == 719579620931797002:
		await db.set_last_general_duel(message.guild.id)
	asyncio.ensure_future(duel_wait_for(message.client, message.channel, message.author, opponent))
	await message.channel.send('Duel starting in 10 seconds... First person to type :gun: once the countdown ends, wins.')
	await asyncio.sleep(5)
	while not duel_statuses[duel_id]['zero']:
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('5')
			await asyncio.sleep(1)
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('4')
			await asyncio.sleep(1)
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('3')
			await asyncio.sleep(1)
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('2')
			await asyncio.sleep(1)
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			await message.channel.send('1')
			await asyncio.sleep(1)
		if (duel_id in duel_statuses) and (not duel_statuses[duel_id]['zero']):
			if random.randint(0, 9) == 0 and False:
				await message.channel.send('sike')
				await asyncio.sleep(5)
			else:
				await message.channel.send('Shoot')
				if duel_id in duel_statuses:
					duel_statuses[duel_id]['zero'] = True
					duel_statuses[duel_id]['ended'] = True
					if opponent.id == 719348452491919401:
						await message.channel.send(':gun:')
		else:
			if duel_id in duel_statuses:
				duel_statuses[duel_id]['zero'] = True
		await asyncio.sleep(1)
	if message.author.id in active_duelers:
		active_duelers.remove(message.author.id)
	if opponent.id in active_duelers:
		active_duelers.remove(opponent.id)
