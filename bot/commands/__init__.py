from ..discordbot import (
	betterbot,
	client,
	has_role,
	mute_user,
	unmute_user
)
from ..betterbot import (
	Member,
	Time
)
from ..	import hypixel
from .. import forums
from .. import db
from .. import modbot
import discord
from discord.ext import commands
import json
from datetime import datetime, timedelta
import io
from contextlib import redirect_stdout
import time
import traceback
import aiohttp
import random
import asyncio
from urllib.parse import quote_plus
import os
import importlib
import sys


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
	print('Registered modular function', module_filename)

bot_owners = {
	224588823898619905 # mat
}

s = aiohttp.ClientSession()

confirmed_emoji = '👍'

with open('roles.json', 'r') as f:
	roles = json.loads(f.read())

with open('doors.json', 'r') as f:
	doors = json.loads(f.read())

with open('tables.json', 'r') as f:
	tables = json.loads(f.read())

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
		time_string = f'1 hour'
	elif minutes >= 2:
		time_string = f'{minutes} minutes'
	elif minutes == 1:
		time_string = f'1 minute'
	elif seconds == 1:
		time_string = f'1 second'
	else:
		time_string = f'{seconds} seconds'
	print('remaining_seconds', remaining_seconds)
	if remaining_seconds > 1 and extra_parts != 0:
		time_string = time_string + ' and ' + seconds_to_string(remaining_seconds, extra_parts=extra_parts - 1)
	return time_string


def get_role_id(guild_id, rank_name):
	return roles.get(str(guild_id), {}).get(rank_name)


@betterbot.command(name='gulag')
async def gulag(message, length: Time=60):
	'Mutes you for one minute'
	mute_remaining = int((await db.get_mute_end(message.author.id)) - time.time())
	if mute_remaining > 0:
		return await message.send('You are already in gulag')
	if length < 60:
		return await message.send('You must be in gulag for at least 60 seconds')
	if length > 60 * 15:
		return await message.send('You can only be in gulag for up to 15 minutes')
	length = int(length)
	if length // 60 > 1:
		await message.send(f'You have entered gulag for {length // 60} minutes.')
	else:
		await message.send(f'You have entered gulag for {length} seconds.')
	
	await mute_user(
		message.author,
		length,
		message.guild.id if message.guild else None
	)

@betterbot.command(name='infractions', bot_channel=False)
async def infractions(message, member: Member=None):
	'Checks the infractions that a user has (mutes, warns, bans, etc)'

	if not member:
		member = message.author

	is_checking_self = message.author.id == member.id
	
	if (
		not is_checking_self
		and not has_role(message.author.id, 717904501692170260, 'helper')
		and not has_role(message.author.id, 717904501692170260, 'trialhelper')
	):
		return

	infractions = await db.get_infractions(member.id)

	embed_title = 'Your infractions' if is_checking_self else f'{member}\'s infractions'

	embed = discord.Embed(
		title=embed_title
	)
	for infraction in infractions[-30:]:
		value = infraction.get('reason') or '<no reason>'
		name = infraction['type']
		if 'date' in infraction:
			date_pretty = infraction['date'].strftime('%m/%d/%Y')
			name += f' ({date_pretty})'
		if len(value) > 1000:
			value = value[:1000] + '...'
		embed.add_field(
			name=name,
			value=value,
			inline=False
		)

	if len(infractions) == 0:
		embed.description = 'No infractions'

	if is_checking_self:
		await message.author.send(embed=embed)
		await message.add_reaction(confirmed_emoji)
	else:
		await message.send(embed=embed)


@betterbot.command(name='clearinfractions', bot_channel=False)
async def clearinfractions(message, member: Member, date: str=None):
	'Checks the infractions that a user has (mutes, warns, bans, etc)'

	if (
		not has_role(message.author.id, 717904501692170260, 'helper')
		and not has_role(message.author.id, 717904501692170260, 'trialhelper')
	):
		return

	if not member or not date:
		return await message.send('Please use `!clearinfractions @member date`')
	# month, day, year = date.split('/')
	if date == 'today':
		date = datetime.now()
	else:
		try:
			date = datetime.strptime(date.strip(), '%m/%d/%Y')
		except ValueError:
			return await message.send('Invalid date (use format mm/dd/yyyy)')
	cleared = await db.clear_infractions(member.id, date)

	if cleared > 1:
		return await message.send(f'Cleared {cleared} infractions from that date.')
	if cleared == 1:
		return await message.send('Cleared 1 infraction from that date.')
	else:
		return await message.send('No infractions found from that date.')

@betterbot.command(name='clearrecentinfraction', aliases=['clearnewinfraction'], bot_channel=False)
async def clear_recent_infraction(message, member: Member):
	if (
		not has_role(message.author.id, 717904501692170260, 'helper')
		and not has_role(message.author.id, 717904501692170260, 'trialhelper')
	):
		return

	if not member:
		return await message.send('Please use `!clearrecentinfraction @member`')
	await db.clear_recent_infraction(member.id)

	await message.add_reaction(confirmed_emoji)


def execute(_code, loc):  # Executes code asynchronously
	_code = _code.replace('\n', '\n ')
	globs = globals()
	globs.update(loc)
	exec(
		'async def __ex():\n ' + _code,
		globs
	)
	return globs['__ex']()

@betterbot.command(name='exec', aliases=['eval'], bot_channel=False)
async def execute_command(message, code: str):
	if message.author.id != 224588823898619905: return
	f = io.StringIO()
	with redirect_stdout(f):
		command = message.content.split(None, 1)[1].strip()
		if command.startswith('```') and command.endswith('```'):
			command = '\n'.join(command.split('\n')[1:])
			command = command[:-3]
		try:
			output = await execute(command, locals())
		except Exception as e:
			traceback.print_exc()
	out = f.getvalue()
	if out == '':
		# out = 'No output.'
		return
	await message.send(
		embed=discord.Embed(
			title='Eval',
			description=out
		)
	)


@betterbot.command(name='setcounting')
async def counting_channel(message, value):
	if message.author.id != 224588823898619905: return
	await db.set_counter(message.guild.id, int(value))
	await message.channel.send('ok')


@betterbot.command(name='counting', aliases=['counter'])
async def get_counting(message, value):
	counter = await db.get_counter(message.guild.id)
	await message.channel.send(counter)


@betterbot.command(name='help', aliases=['commands'])
async def help_command(message):
	help_commands = [
		{
			'name': 'link',
			'args': '<ign>',
			'desc': 'Links your Discord account to your Minecraft account and gives you Hypixel rank roles',
		},
		{
			'name': 'e',
			'args': '',
			'desc': 'e',
		},
		{
			'name': 'gulag',
			'args': '',
			'desc': 'Puts you in gulag for one minute',
		},
		{
			'name': 'rock',
			'args': '@member',
			'desc': "Extends the length of a user's time in gulag by 5 minutes",
		},
		{
			'name': 'forum user',
			'args': '<username>',
			'desc': 'Gets the forum stats for a username',
		},
		{
			'name': 'forum thread',
			'args': '<id>',
			'desc': 'Shows a forum thread',
		},
		{
			'name': 'tictactoe',
			'args': '[@member]',
			'desc': 'Lets you play tic-tac-toe against another member or against AI',
		},
		{
			'name': 'shitpost',
			'args': '',
			'desc': 'Generates a shitpost using a markov chain',
		},
		{
			'name': 'duel',
			'args': '[@member]',
			'desc': 'Duels a member',
		},
	]

	if has_role(message.author.id, 717904501692170260, 'helper'):
		help_commands.extend([
			{
				'name': 'mute',
				'args': '@member <length> [reason]',
				'desc': 'Mutes a user from sending messages for a certain amount of time',
			},
			{
				'name': 'unmute',
				'args': '@member',
				'desc': 'Unmutes a user early so they can send messages',
			},
			{
				'name': 'infractions',
				'args': '@member',
				'desc': 'View the infractions of another member (mutes, warns, etc)',
			},
			{
				'name': 'clearinfractions',
				'args': '@member <mm/dd/yyyy>',
				'desc': 'Clear the infractions for a member from a specific date',
			}
		])
	else:
		help_commands.extend([
			{
				'name': 'infractions',
				'args': '',
				'desc': 'View your own infractions (mutes, warns, etc)',
			}
		])

	description = []

	for command in help_commands:
		command_name = command['name']
		command_args = command['args']
		command_desc = command['desc']
		if command_args:
			command_title = f'!**{command_name}** {command_args}'
		else:
			command_title = f'!**{command_name}**'
		description.append(
			f'{command_title} - {command_desc}'
		)

	embed = discord.Embed(title='Commands', description='\n'.join(description))
	await message.send(embed=embed)


@betterbot.command(name='membercount', aliases=['members'])
async def membercount(message, command, user):
	true_member_count = message.guild.member_count
	await message.channel.send(
		f'There are **{true_member_count:,}** people in this server.'
	)


# !forum
@betterbot.command(name='forum', aliases=['forums', 'f'], pad_none=False)
async def forum(message):
	await message.send('Forum commands: **!forums user (username)**')

forum_ratelimit = {}


def check_forum_ratelimit(user):
	global forum_ratelimit
	if user not in forum_ratelimit: return False
	user_ratelimit = forum_ratelimit[user]
	last_minute_uses = 0
	last_10_second_uses = 0
	last_3_second_uses = 0
	for ratelimit in user_ratelimit:
		if time.time() - ratelimit < 60:
			last_minute_uses += 1
			if time.time() - ratelimit < 10:
				last_10_second_uses += 1
				if time.time() - ratelimit < 10:
					last_3_second_uses += 1
		else:
			del user_ratelimit[0]
	print('last_minute_uses', last_minute_uses)
	print('last_10_second_uses', last_10_second_uses)
	if last_minute_uses >= 10: return True
	if last_10_second_uses >= 3: return True
	if last_3_second_uses >= 2: return True
	return False

def add_forum_ratelimit(user):
	global forum_ratelimit
	if user not in forum_ratelimit:
		forum_ratelimit[user] = []
	forum_ratelimit[user].append(time.time())
	print('forum_ratelimit', forum_ratelimit)


# !forum user
@betterbot.command(name='forum', aliases=['forums', 'f'], pad_none=False)
async def forum_user(message, command, user):
	if command not in {
		'member',
		'user',
	}:
		raise TypeError

	if check_forum_ratelimit(message.author.id):
		print('no')
		return await message.send('Stop spamming the command, nerd')
	add_forum_ratelimit(message.author.id)


	async with message.channel.typing():
		member_id = await forums.member_id_from_name(user)
		if not member_id:
			return await message.send('Invalid user.')
		print('member_id', member_id)
		member = await forums.get_member(member_id)


		total_messages = member['messages']
		follower_count = member.get('follower_count')
		positive_reactions = member['reactions']['positive_total']
		member_name = member['name']
		member_id = member['id']
		avatar_url = member['avatar_url']

		description = (
			f'Messages: {total_messages:,}\n'
			+ (f'Followers: {follower_count:,}\n' if follower_count is not None else '')
			+ f'Reactions: {positive_reactions:,}\n'
		)


		embed = discord.Embed(
			title=f"{member_name}'s forum stats",
			description=description,
			url=f'https://hypixel.net/members/{member_id}/'
		)

		if follower_count is None:
			embed.set_footer(text='This member limits who may view their full profile.')


		embed.set_thumbnail(url=avatar_url)


		await message.channel.send(embed=embed)

def trim_string(string, width=150, height=20):
	# shortens a string and adds ellipses if it's too long
	was_trimmed = False
	new_string = ''
	x_pos = 0
	y_pos = 0
	for character in string:
		if character == '\n':
			y_pos += 1
			x_pos = 0
		x_pos += 1
		if x_pos > width:
			y_pos += 1
			x_pos = 0
		if y_pos > height:
			was_trimmed = True
			break
		new_string += character

	if was_trimmed:
		new_string += '...'
	return new_string

# !forum thread
@betterbot.command(name='forum', aliases=['forums', 'f'], pad_none=False, bot_channel=False)
async def forum_user(message, command, thread_id: int):
	if command not in {
		'post',
		'thread',
	}:
		raise TypeError

	if message.guild and message.channel.id not in {
		718139355813904484, # forum threads channel
		718076311150788649, # bot-commands
		719518839171186698, # staff-bot-commands
	}:
		print('bad channel', message.channel.id)
		return

	if check_forum_ratelimit(message.author.id):
		return await message.send('Stop spamming the command, nerd')
	add_forum_ratelimit(message.author.id)

	print('ok')
	async with message.channel.typing():
		thread = await forums.get_thread(thread_id)
		if not thread:
			return await message.send('Invalid thread.')
		body_trimmed = trim_string(thread['body'])
		embed = discord.Embed(
			title=thread['title'],
			description=body_trimmed,
			url=thread['url']
		)
		embed.set_author(
			name=thread['author']['name'],
			url=thread['author']['url'],
			icon_url=thread['author']['avatar_url'],
		)
		if thread['image']:
			embed['image'] = {
				'url':  thread['image']
			}
		await message.channel.send(embed=embed)


@betterbot.command(name='pee', bot_channel=False)
async def pee(message):
	'pees in gulag'

	if message.channel.id != 720073985412562975: return

	await message.channel.send('You have peed.')

@betterbot.command(name='poo', aliases=['poop'], bot_channel=False)
async def poop(message):
	'poops in gulag'

	if message.channel.id != 720073985412562975: return

	await message.channel.send('You have pooped.')

@betterbot.command(name='rock', aliases=['stone'], bot_channel=False)
async def throw_rock(message, member: Member):
	"Adds 5 minutes to someone's mute in gulag"

	if message.channel.id not in {
		720073985412562975, # gulag
		718076311150788649, # bot-commands
	}: return

	if not member:
		return await message.send('Unknown member. Example usage: **!rock pigsty**')

	if member == message.author.id:
		return await message.send("You can't throw a rock at yourself.")

	mute_end = await db.get_mute_end(member.id)
	if not (mute_end and mute_end > time.time()):
		return await message.send('This person is not in gulag.')
	mute_remaining = mute_end - time.time()

	print('mute_remaining')


	# makes sure people havent thrown a rock in the last hour
	last_rock_thrown = await db.get_rock(message.author.id)
	# if message.author.id == 224588823898619905:
	# 	last_rock_thrown = 0
	print('last_rock_thrown', last_rock_thrown)
	if time.time() - last_rock_thrown < 60 * 60:
		next_rock_seconds = (60 * 60) - int(time.time() - last_rock_thrown)
		next_rock_minutes = next_rock_seconds // 60
		if next_rock_minutes >= 2:
			next_rock_str = f'{next_rock_minutes} minutes'
		elif next_rock_minutes == 1:
			next_rock_str = f'one minute'
		elif next_rock_seconds == 1:
			next_rock_str = f'one second'
		else:
			next_rock_str = f'{next_rock_seconds} seconds'
		return await message.send(f'You threw a rock too recently. You can throw a rock again in {next_rock_str}')

	bobux = await db.get_bobux(message.author.id)
	if bobux < 2:
		return await message.send('You need at least 2 bobux to use !rock')
	await db.change_bobux(message.author.id, -2)

	await db.set_rock(message.author.id)

	# Add 5 minutes to someone's mute
	new_mute_remaining = int(mute_remaining + (60 * 5))

	print('muting again')

	new_mute_remaining_minutes = int(new_mute_remaining // 60)
	new_mute_remaining_hours = int(new_mute_remaining_minutes // 60)
	if new_mute_remaining_hours >= 2:
		new_mute_str = f'{new_mute_remaining_hours} hours'
	elif new_mute_remaining_hours == 1:
		new_mute_str = f'one hour'
	elif new_mute_remaining_minutes >= 2:
		new_mute_str = f'{new_mute_remaining_minutes} minutes'
	elif new_mute_remaining_minutes == 1:
		new_mute_str = f'one minute'
	elif new_mute_remaining == 1:
		new_mute_str = f'one second'
	else:
		new_mute_str = f'{new_mute_remaining} seconds'
	await message.send(f'<@{member.id}> is now muted for {new_mute_str}')

	await discordbot.mute_user(
		member,
		new_mute_remaining,
		717904501692170260
	)

@betterbot.command(name='mutelength', aliases=['mutetime'], bot_channel=False)
async def mute_length(message, member: Member=None):
	if message.channel.id not in {
		720073985412562975, # gulag
		718076311150788649, # bot-commands
		719518839171186698, # staff-bot-commands
	}: return

	if not member:
		member = message.author

	mute_remaining = int((await db.get_mute_end(member.id)) - time.time())

	if mute_remaining < 0:
		await discordbot.unmute_user(member.id, True, False)
		if member.id == message.author.id:
			await message.send(embed=discord.Embed(
				description="You aren't muted."
			))
		else:
			await message.send(embed=discord.Embed(
				description=f"<@{member.id}> isn't muted."
			))
	else:
		mute_str = seconds_to_string(mute_remaining)
		if member.id == message.author.id:
			await message.send(embed=discord.Embed(
				description=f'You are muted for {mute_str}'
			))
		else:
			await message.send(embed=discord.Embed(
				description=f'<@{member.id}> is muted for {mute_str}'
			))

@betterbot.command(name='stackdandelion', aliases=['stackdandelions', 'fixdandelionstacking'])
async def fix_dandelion_stacking(message):
	if not fix_dandelion_stacking.fixed:
		await message.send('Dandelion stacking has been fixed.')
	else:
		await message.send('Dandelion stacking is now broken again.')
	fix_dandelion_stacking.fixed = not fix_dandelion_stacking.fixed
fix_dandelion_stacking.fixed = False


# @betterbot.command(name='giveaway', bot_channel=False)
# async def start_giveaway(message, length, prize):
# 	if not has_role(message.author.id, 717904501692170260, 'helper'): return


@betterbot.command(name='duck', aliases=['duckpic', 'randomduck', 'duckpicture'], bot_channel=False)
async def random_duck(message):
	if message.channel.id not in {
		720073985412562975, # gulag
		718076311150788649, # bot-commands
		719518839171186698, # staff-bot-commands
	} and message.guild: return

	show = 'duck'

	if message.channel.id == 720073985412562975: # gulag
		show = random.choice(['duck', 'no'])

	if show == 'duck':
		async with s.get('https://random-d.uk/api/random') as r:
			data = await r.json()
			url = data['url']
	else:
		url = 'https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4a9.png'
	embed = discord.Embed(title='Random duck')
	embed.set_image(url=url)
	await message.channel.send(embed=embed)

@betterbot.command(name='door', aliases=['doorpic', 'randomdoor', 'doors'])
async def random_door(message):
	url = random.choice(doors)
	embed = discord.Embed(title='Random door')
	embed.set_image(url=url)
	await message.channel.send(embed=embed)

@betterbot.command(name='table', aliases=['tablepic', 'randomtable', 'tables'])
async def random_table(message):
	url = random.choice(tables)
	embed = discord.Embed(title='Random table')
	embed.set_image(url=url)
	await message.channel.send(embed=embed)


@betterbot.command(name='avatar')
async def get_discord_avatar(message, member: Member):
	await message.channel.send(member.avatar_url)

@betterbot.command(name='toxicity')
async def check_toxicity(message, check_message: str):
	data = await modbot.get_perspective_score(check_message)
	score = data['SEVERE_TOXICITY']
	await message.channel.send(f'Severe toxicity: {int(score*10000)/100}%')

@betterbot.command(name='keyboardsmash')
async def check_keyboardsmash(message, check_message: str):
	score = modbot.get_keyboard_smash_score(check_message)
	await message.channel.send(f'Score: {score}')


@betterbot.command(name='b')
async def bagel(message):
	await message.channel.send('I like french bread')


@betterbot.command(name='bleach')
async def bleach(message):
	embed = discord.Embed(
		title="Here's a Clorox bleach if you want to unsee something weird:"
	)
	embed.set_image(url='https://cdn.discordapp.com/attachments/741200821936586785/741200842430087209/Icon_3.jpg')
	await message.channel.send(embed=embed)


@betterbot.command(name='wow')
async def wow(message):
	await message.author.send('https://im-a-puzzle.com/look_i_m_a_puzzle_4XZqEhin.puzzle')
	await message.delete()

rigged_duel_users = set()

@betterbot.command(name='rigduel', aliases=['rigduels'], bot_channel=False)
async def rig_duel_command(message, member: Member=None):
	if message.author.id != 224588823898619905: return # only works for mat
	rigged_duel_users.add(member.id if member else message.author.id)
	await message.delete()

duel_statuses = {}
active_duelers = set()

async def duel_wait_for(channel, opponent_1, opponent_2):
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
	if channel.id == 750147192383078400: # quaglet channel
		mute_length = 0
	elif channel.id == 719579620931797002: # general
		mute_length = 60 * 60
		try:
			await duel_loser.send("You were muted for one hour because you lost a duel in general")
		except: pass
		print(2)
	elif channel.id == 720073985412562975: # gulag
		mute_end = await db.get_mute_end(duel_loser.id)
		mute_remaining = mute_end - time.time()
		mute_length = mute_remaining + 60 * 5
	else:
		mute_length = 60 * 1
		try:
			await duel_loser.send("You were muted for one minute because you lost a duel")
		except: pass
	try:
		del duel_statuses[duel_id]
	except KeyError:
		pass
	if opponent_1.id in active_duelers:
		active_duelers.remove(opponent_1.id)
	if opponent_2.id in active_duelers:
		active_duelers.remove(opponent_2.id)

	if mute_length > 0:
		await discordbot.mute_user(
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

@betterbot.command(name='duel', bot_channel=False)
async def duel(message, opponent: Member):
	if message.channel.id not in {
		719579620931797002, # general
		718076311150788649, # bot-commands
		720073985412562975, # gulag
		750147192383078400, # quaglet channel
	}: return
	# if message.channel.id == 719579620931797002:
	# 	last_duel = await db.get_last_general_duel(message.guild.id)
	# 	if last_duel:
	# 		time_since_last_duel = datetime.now() - last_duel
	# 		if time_since_last_duel < timedelta(hours=1):
	# 			return await message.channel.send('There can only be one duel in general per hour.')
	# get_last_general_duel
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
			reaction, user = await client.wait_for(
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
	asyncio.ensure_future(duel_wait_for(message.channel, message.author, opponent))
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
