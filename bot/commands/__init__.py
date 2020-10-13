from ..discordbot import (
	betterbot,
	client,
	has_role,
)
from ..betterbot import (
	Member,
)
from urllib.parse import quote_plus
import importlib
import aiohttp
import discord
import asyncio
import forums
import modbot
import random
import json
import time
import os
import db


print('commands.py')


command_modules = []
for module_filename in os.listdir('./bot/commands'):
	if module_filename == '__init__.py' or module_filename[-3:] != '.py':
		continue
	module = importlib.import_module('bot.commands.' + module_filename[:-3])
	command_modules.append(module)
	betterbot.command(
		module.name,
		aliases=getattr(module, 'aliases', []),
		bot_channel=getattr(module, 'bot_channel', None),
		pad_none=getattr(module, 'pad_none', None),
	)(module.run)
	print('Registered command from file', module_filename)

bot_owners = {
	224588823898619905  # mat
}

s = aiohttp.ClientSession()

confirmed_emoji = '👍'

with open('roles.json', 'r') as f:
	roles = json.loads(f.read())

with open('suntzu.json', 'r') as f:
	suntzu_quotes = json.loads(f.read())


def seconds_to_string(actual_seconds, extra_parts=1):
	seconds = int(actual_seconds)
	minutes = int(actual_seconds // 60)
	hours = int(actual_seconds // (60 * 60))
	remaining_seconds = actual_seconds
	if hours > 0:
		remaining_seconds -= hours * 60 * 60
	elif minutes > 0:
		remaining_seconds -= minutes * 60
	elif seconds > 0:
		remaining_seconds -= seconds

	if hours >= 2:
		time_string = f'{hours} hours'
	elif hours == 1:
		time_string = '1 hour'
	elif minutes >= 2:
		time_string = f'{minutes} minutes'
	elif minutes == 1:
		time_string = '1 minute'
	elif seconds == 1:
		time_string = '1 second'
	else:
		time_string = f'{seconds} seconds'
	print('remaining_seconds', remaining_seconds)
	if remaining_seconds > 1 and extra_parts != 0:
		time_string = time_string + ' and ' + seconds_to_string(remaining_seconds, extra_parts=extra_parts - 1)
	return time_string


def get_role_id(guild_id, rank_name):
	return roles.get(str(guild_id), {}).get(rank_name)


		

# amongus_cooldown = {}
# amongus_active = False
# last_amongus = 0

# @betterbot.command(name='amongus', aliases=['votingsim', 'votingsimulator'], bot_channel=False)
# async def amongus_command(message):
# 	global amongus_active
# 	global last_amongus
# 	if message.channel.id == 718076311150788649: # bot commands
# 		return await message.channel.send('This command only works in <#719579620931797002>')
# 	if message.channel.id != 719579620931797002: # general
# 		return
# 	if not (
# 		has_role(message.author.id, 717904501692170260, 'helper')
# 		or has_role(message.author.id, 717904501692170260, 'trialhelper')
# 		or has_role(message.author.id, 717904501692170260, 'sweat')
# 	):
# 		return await message.channel.send('You must be a sweat or staff member to start a game of Among Us')
# 	if amongus_active:
# 		return await message.channel.send('There is already a game of Among Us active')
# 	if time.time() - last_amongus < 60 * 30:
# 		return await message.channel.send('A game of Among Us already happened too recently')
# 	amongus_active = True
# 	players = []
# 	async for message in message.channel.history(limit=500):
# 		# make sure message has been created in past 15 minutes
# 		if message.created_at > datetime.now() - timedelta(minutes=5):
# 			# dont duplicate players
# 			if message.author not in players:
# 				players.append(message.author)
# 			# max of 8 players
# 			if len(players) >= 8:
# 				break
# 	# players 
# 	if len(players) < 4:
# 		amongus_active = False
# 		return await message.channel.send('Chat is too dead right now :pensive:')
# 	countdown_length = 30 # how long the voting period lasts, in seconds
# 	embed = discord.Embed(
# 		title='Who is The Imposter?',
# 		footer=str(countdown_length)
# 	)
# 	keycap_emojis = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣')
# 	for i, player in enumerate(players):
# 		embed.add_field(name=str(player), value=keycap_emojis[i], inline=False)
# 	game_message = await message.channel.send(embed=embed)
# 	for i, player in enumerate(players):
# 		await game_message.add_reaction(keycap_emojis[i])
# 	for countdown in reversed(range(0, countdown_length)):
# 		embed.set_footer(text=str(countdown))
# 		await game_message.edit(embed=embed)
# 		await asyncio.sleep(1)
# 	print('ok counted down')
# 	# fetch the message again to update reaction data
# 	game_message = await game_message.channel.fetch_message(game_message.id)
# 	top_reactions = {}	
# 	total_votes = 0
# 	for reaction in game_message.reactions:
# 		print(reaction, reaction.emoji)
# 		if reaction.emoji in keycap_emojis:
# 			top_reactions[reaction.emoji] = reaction.count - 1 # -1 because initial bot reaction
# 			total_votes += reaction.count - 1
# 	print('total_votes', total_votes)
# 	if total_votes < 4:
# 		amongus_active = False
# 		return await message.channel.send('Not enough votes')
# 	# await message.channel.send(embed=discord.Embed(description=str(top_reactions)))
# 	highest_reaction_user = None
# 	highest_reaction_count = 0
# 	is_tie = False
# 	print('gotten reactions', top_reactions)
# 	for i, reaction in enumerate(keycap_emojis):
# 		reaction_count = top_reactions.get(reaction, 0)
# 		if reaction_count == highest_reaction_count:
# 			is_tie = True
# 		elif reaction_count > highest_reaction_count:
# 			highest_reaction_count = reaction_count
# 			highest_reaction_user = players[i]
# 			is_tie = False
# 	print('e', highest_reaction_user)

# 	if is_tie:
# 		amongus_active = False
# 		return await message.channel.send("It's a tie, no one goes to gulag")
# 	else:
# 		amongus_active = False
# 		print('ok muted')
# 		last_amongus = time.time()
# 		await message.channel.send(f'<@{highest_reaction_user.id}> got voted out (5 minutes in gulag)')
# 		mute_end = await db.get_mute_end(highest_reaction_user.id)
# 		if not (mute_end and mute_end > time.time()):
# 			mute_length = 60 * 5
# 		else:
# 			mute_remaining = mute_end - time.time()
# 			mute_length = (60 * 5) + mute_remaining

# 		await discordbot.mute_user(
# 			highest_reaction_user,
# 			mute_length,
# 			message.guild.id if message.guild else None
# 		)

# 	# return await message.channel.send('You must be a sweat or staff member to start a game of Among Us')
	




# 	# amongus_cooldown[message.author.id] = time.time()

@betterbot.command(name='suntzu')
async def suntzu_quote(message, extra: str=None):
	embed = discord.Embed()
	quote_text = extra or random.choice(suntzu_quotes)['text']
	embed.set_image(url='https://suntzu.matdoes.dev/quote.png?quote=' + quote_plus(quote_text))
	await message.channel.send(embed=embed)

@betterbot.command(name='bobux')
async def show_bobux(message, member: Member=None):
	print('bobux', member)
	if not member:
		member = message.author
	bobux = await db.get_bobux(member.id)
	if member.id == message.author.id:
		bobux_message = f'You have **{bobux}** bobux'
	else:
		bobux_message = f'<@{member.id}> has **{bobux}** bobux'
	print(bobux_message)
	embed = discord.Embed(
		# title='Bobux',
		description=bobux_message
	)
	await message.channel.send(embed=embed)

@betterbot.command(name='givebobux', bot_channel=False)
async def give_bobux(message, member: Member=None, amount: int=0):
	if not has_role(message.author.id, 717904501692170260, 'admin'): return
	if not member:
		return await message.channel.send('invalid member')
	if not amount:
		return await message.channel.send('invalid amount')
	await db.change_bobux(member.id, amount)
	await message.channel.send('ok')
