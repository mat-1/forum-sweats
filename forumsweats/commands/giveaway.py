from datetime import datetime
from forumsweats.commandparser import Context, Member, Time
from utils import seconds_to_string
from typing import Any, Callable
from forumsweats.discordbot import client
from forumsweats import db
import discord
import asyncio
import random
import time

name = 'giveaway'
roles = ('mod',)
channels = None


GIVEAWAY_EMOJI = '🎉'


async def update_giveaway_message(message: discord.Message, data: dict, winners=None):
	embed = create_giveaway_embed(data, winners=winners)

	# if there's a winner, make the content be "giveaway ended"
	if winners:
		await message.edit(content='🎉 **GIVEAWAY ENDED** 🎉', embed=embed)
	else:
		await message.edit(embed=embed)


async def end_giveaway(data: dict):
	await db.end_giveaway(data['id'])

	channel = client.get_channel(data['channel_id'])
	message = await channel.fetch_message(data['id'])
	total_winners = data['winners']
	prize = data['prize']
	creator_id = data['creator_id']
	bobux_requirement = data['bobux_requirement']

	# find all the members that reacted to the giveaway
	reacted_users = []

	for reaction in message.reactions:
		if reaction.emoji == GIVEAWAY_EMOJI:
			async for user in reaction.users():
				if not user.bot:
					if bobux_requirement > 0:
						member_bobux = await db.get_bobux(user.id)
						if member_bobux < bobux_requirement:
							continue
					reacted_users.append(user)
	
	if len(reacted_users) >= total_winners:
		# Choose the winner!
		winners = random.sample(reacted_users, total_winners)
	else:
		winners = 'Not enough people reacted :('

	await update_giveaway_message(message, data, winners)

	if not isinstance(winners, list): return

	winner_mentions = ' '.join(winner.mention for winner in winners)

	await channel.send(winner_mentions)
	for winner in winners:
		try:
			await winner.send(f'You won **{prize}** {message.jump_url}')
		except:
			# if they blocked the bot, just continue
			pass

	creator = client.get_user(creator_id)
	await creator.send(f'The following members won **{prize}**: {winner_mentions}')


async def continue_giveaway(data: dict):
	time_left: int = data['end'] - int(time.time())

	time_left_string: str = seconds_to_string(time_left)
	time_left_string_before: str = ''

	channel = client.get_channel(data['channel_id'])
	message = await channel.fetch_message(data['id'])

	while time_left > 0:
		# If it's gonna end in more than a minute, update every 30 seconds
		if time_left > 60:
			await asyncio.sleep(30)
		# If it's gonna end in more than 3 seconds, update every 2 seconds
		elif time_left > 3:
			await asyncio.sleep(2)
		# If it's gonna end in less than 3 seconds, update every second
		else:
			await asyncio.sleep(1)

		time_left = data['end'] - int(time.time())
		time_left_string = seconds_to_string(time_left)
		if time_left_string != time_left_string_before:
			await update_giveaway_message(message, data)
			time_left_string_before = time_left_string

	await update_giveaway_message(message, data)
	await end_giveaway(data)


async def continue_giveaways():
	active_giveaways = await db.get_active_giveaways()
	for giveaway_data in active_giveaways:
		asyncio.ensure_future(continue_giveaway(giveaway_data), loop=client.loop)


def create_giveaway_embed(data: dict, winners=None):
	prize = data['prize']
	creator_id = data['creator_id']
	end = data['end']
	winner_count = data['winners']
	bobux_requirement = data['bobux_requirement']

	ended = time.time() > end

	if ended:
		if winners is None:
			description = f'**Winner: ...**'
		elif isinstance(winners, str):
			description = f'**Winner: {winners}**'
		elif len(winners) > 1:
			winners_mentions = ', '.join(winner.mention for winner in winners)
			description = f'**Winners: {winners_mentions}**'
		else:
			description = f'**Winner: {winners[0].mention}**'
	else:
		ends_in_string = seconds_to_string(end - int(time.time()))
		description = f'**Ends in: {ends_in_string}**'
		if winner_count != 1:
			description += f'Winners: {winner_count}'
		if bobux_requirement > 0:
			description += f'Requirement: {bobux_requirement} bobux'

	description += f'\nHosted by: <@{creator_id}>'

	embed = discord.Embed(
		title=prize,
		description=description,
		timestamp=datetime.fromtimestamp(end)
	)

	return embed


async def create_new_giveaway(creator_id: int, channel: discord.abc.GuildChannel, length: int, winners: int, bobux_requirement: int, prize: str):
	end = int(time.time() + length)

	embed = create_giveaway_embed({
		'creator_id': creator_id,
		'channel_id': channel.id, # type: ignore (the typings on discord.py are wrong)
		'end': end,
		'winners': winners,
		'bobux_requirement': bobux_requirement,
		'prize': prize,
		'ended': False
	})

	giveaway_message = await channel.send('🎉 **GIVEAWAY** 🎉', embed=embed) # type: ignore (the typings on discord.py are wrong)
	await giveaway_message.add_reaction(GIVEAWAY_EMOJI)

	giveaway_data = await db.create_new_giveaway(
		message_id=giveaway_message.id,
		creator_id=creator_id,
		channel_id=channel.id, # type: ignore (the typings on discord.py are wrong)
		end=end,
		winners=winners,
		bobux_requirement=bobux_requirement,
		prize=prize,
	)

	asyncio.ensure_future(continue_giveaway(giveaway_data), loop=client.loop)


async def prompt_input(client: discord.Client, user: Member, channel: discord.abc.Messageable, prompt_message: str, invalid_message: str, check: Callable[[str], Any]) -> Any:
	user_response = None

	await channel.send(prompt_message)

	while user_response is None:
		m: discord.Message = await client.wait_for('message', check=lambda m: m.author.id == user.id, timeout=60)

		if m.content.lower() == 'cancel':
			return await m.add_reaction('👍')
		
		user_response = await check(m.content)

		if user_response is None:
			await channel.send(invalid_message + ' (Type "cancel" to cancel the giveaway creation)')
	return user_response


async def run(message: Context):
	async def check_channel(content: str):
		if not (content.startswith('<#') and content.endswith('>')):
			return
		channel_id = content[2:-1]
		try: channel_id = int(channel_id)
		except: return
		channel = message.client.get_channel(channel_id)
		return channel

	channel: discord.abc.GuildChannel = await prompt_input(
		message.client,
		message.author,
		message.channel,
		prompt_message='Please mention the channel to do the giveaway in.',
		invalid_message='Invalid channel.',
		check=check_channel
	)
	if channel is None: return


	async def check_duration(content: str):
		return await Time().convert(message, content)

	length: int = await prompt_input(
		message.client,
		message.author,
		message.channel,
		prompt_message='How long should the giveaway last?',
		invalid_message='Invalid time.',
		check=check_duration
	)
	if length is None: return


	async def check_winners(content: str):
		try: return int(content)
		except: return

	winners: int = await prompt_input(
		message.client,
		message.author,
		message.channel,
		prompt_message='How many winners are there?',
		invalid_message='Invalid number.',
		check=check_winners
	)
	if winners is None: return


	async def check_bobux_requirement(content: str):
		try: return int(content)
		except: return

	bobux_requirement: int = await prompt_input(
		message.client,
		message.author,
		message.channel,
		prompt_message='How much bobux should you need to enter? (Enter 0 for no requirement)',
		invalid_message='Invalid number.',
		check=check_bobux_requirement
	)
	if bobux_requirement is None: return


	async def check_prize(content: str):
		return content

	prize: str = await prompt_input(
		message.client,
		message.author,
		message.channel,
		prompt_message='What\'s the prize for the giveaway? (This will start the giveaway)',
		invalid_message='Invalid prize.',
		check=check_prize
	)
	if prize is None: return

	await create_new_giveaway(message.author.id, channel, length, winners, bobux_requirement, prize)
