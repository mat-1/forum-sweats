from forumsweats.commandparser import Context, Member, Time
from forumsweats.discordbot import client
from discord.reaction import Reaction
from discord.message import Message
from utils import seconds_to_string
from typing import Any, Callable
from discord.user import User
from datetime import datetime
from forumsweats import db
import discord
import asyncio
import time

name = 'auction'
roles = ('mod', 'helper')
channels = None
args = ''


AUCTION_EMOJI = '💸'


def create_auction_embed(data: dict, bidder=None):
	item = data['item']
	creator_id = data['creator_id']
	end = data['end']
	highest_bidder = bidder or data.get('highest_bidder')
	current_bid = data.get('highest_bid', 0)

	ended = time.time() > end

	if isinstance(highest_bidder, (str, list, tuple)):
		highest_bidder = highest_bidder[0]	

	description = f'Highest bid is {current_bid}. Minimal next bid {current_bid + 100} bobux'
	if highest_bidder:
		description = f'Highest bid is {current_bid} by <@{highest_bidder}>. Minimal next bid {current_bid + 100} bobux'

	description += f'\nReact with {AUCTION_EMOJI} to bid\n'

	if ended:
		if highest_bidder is None:
			description = f'**No highest bidder**'
		else:
			description = f'**The highest bid was: {current_bid} by <@{highest_bidder}>**'
	else:
		ends_in_string = seconds_to_string(end - int(time.time()))
		description += f'**Ends in: {ends_in_string}**'
	description += f'\nHosted by: <@{creator_id}>'
	

	embed = discord.Embed(
		title=item,
		description=description,
		timestamp=datetime.fromtimestamp(end)
	)

	return embed


async def update_auction_message(message: discord.Message, data: dict = None):
	if not data:
		data = await db.get_auction(message.id)
	embed = create_auction_embed(data)

	if not message: return

	try:
		await message.edit(embed=embed)
	except: # Message dosen't exist
		return	


async def end_auction(data: dict):
	await db.end_auction(data['id'])
	

	channel = client.get_channel(data['channel_id'])
	if not channel: return  # the channel the auction was in was deleted
	message: discord.Message = await channel.fetch_message(data['id'])
	if not message: return  # the message was deleted

	highest_bidder = data.get('highest_bidder')
	highest_bid = data.get('highest_bid', 0)
	if not highest_bidder: return

	#winner = await channel.guild.fetch_member(highest_bidder)

	await db.change_bobux(highest_bidder, -highest_bid)
	


async def continue_auction(message_id: int):
	data = await db.get_auction(message_id)
	time_left: int = data['end'] - int(time.time())

	time_left_string = seconds_to_string(time_left)
	time_left_string_before = ''

	channel = client.get_channel(data['channel_id'])

	# if it can't find the channel, just print a warning and return
	if not channel:
		print(f'Could not find channel for auction {data["id"]}')
		return

	try:
		message = await channel.fetch_message(data['id'])
	except discord.errors.NotFound:
		await db.end_auction(data['id'])
		return
	
	handle_bids(message)


	while time_left > 0:
		data = await db.get_auction(message_id)
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
			try:
				await update_auction_message(message)
			except discord.errors.Forbidden:
				pass
			time_left_string_before = time_left_string

	await update_auction_message(message)
	await end_auction(data)



def handle_bids(message: Message):
	@client.event
	async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
		if not payload.member or payload.member.bot or payload.message_id != message.id: return

		# re-fetch the message so we can remove other reactions
		new_message = await message.channel.fetch_message(payload.message_id)
		assert new_message.guild is not None
		member = await new_message.guild.fetch_member(payload.user_id)
		data = await db.get_auction(message.id)

		# iterate over reactions and remove the ones that weren't made by a bot
		for reaction in new_message.reactions:
			async for reacted_user in reaction.users():
				if not reacted_user.bot:
					await new_message.remove_reaction(reaction.emoji, reacted_user)

		auction_info = await db.get_auction(message.id)
		highest_bid = auction_info['highest_bid'] or 0

		# Check if auction ended
		if auction_info['ended']: return

		# Check if the person has enough bobux
		if not await db.get_bobux(member.id) > highest_bid + 100:
			await member.send('You do not have enough bobux to bid')
			return

		await db.set_highest_bidder(message.id, highest_bid + 100, member.id)
		data['highest_bid'] += 100

		if data.get('end') - int(time.time()) < 30:
			await db.extend_auction(message.id, 100)

		embed = create_auction_embed(data, bidder=member.id)
		await message.edit(embed=embed)

async def create_new_auction(creator_id: int, channel: discord.abc.GuildChannel, length: int, item: str):
	end = int(time.time() + length)

	
	embed = create_auction_embed({
		'creator_id': creator_id,
		'end': end,
		'ended': False,
		'item': item,
	})

	auction_message: discord.Message = await channel.send('💸 **Auction** 💸', embed=embed) # type: ignore (the typings on discord.py are wrong)
	await auction_message.add_reaction(AUCTION_EMOJI)


	auction_data = await db.create_new_auction(
		message_id=auction_message.id,
		creator_id=creator_id,
		channel_id=channel.id,
		end=end,
		item=item,
	)

	asyncio.ensure_future(continue_auction(auction_message.id), loop=client.loop)

	return auction_message


async def prompt_input(client: discord.Client, user: Member, channel: discord.abc.Messageable, prompt_message: str, invalid_message: str, check: Callable[[str], Any]) -> Any:
	user_response = None

	await channel.send(prompt_message)

	while user_response is None:
		m: discord.Message = await client.wait_for(
			'message',
			check=lambda m:
				m.author.id == user.id
				and channel.id == channel.id, # type: ignore (the typings on discord.py are wrong)
			timeout=60
		)

		if m.content.lower() == 'cancel':
			return await m.add_reaction('👍')
		
		user_response = await check(m.content)

		if user_response is None:
			await channel.send(invalid_message + ' (Type "cancel" to cancel the auction creation)')
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
		prompt_message='Please mention the channel to start the auction in.',
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
		prompt_message='How long should the auction last?',
		invalid_message='Invalid time.',
		check=check_duration
	)
	if length is None: return


	async def check_content(content: str):
		return content

	item: str = await prompt_input(
		message.client,
		message.author,
		message.channel,
		prompt_message='What are you auctioning? (This will start the auction)',
		invalid_message='Invalid item.',
		check=check_content
	)
	if item is None: return

	auction_message = await create_new_auction(message.author.id, channel, length, item)

	await message.send(f'Ok, created auction {auction_message.jump_url}')


async def continue_auctions():
	active_auctions = await db.get_active_auctions()
	for auction_data in active_auctions:
		asyncio.ensure_future(continue_auction(auction_data['id']), loop=client.loop)
