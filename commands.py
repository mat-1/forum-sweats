import discord
from discordbot import (
	betterbot,
	client,
	has_role
)
import discordbot
from discord.ext import commands
import hypixel
import db
from betterbot import (
	Member,
	Time
)
import json
from datetime import datetime, timedelta
import io
from contextlib import redirect_stdout
import forums
import time
import traceback
import aiohttp
import random
import tictactoe
import asyncio
import modbot
import markovforums
import deepfry
import ducksweirdclickbaitcommand

bot_owners = {
	224588823898619905, # mat
	# 385506886222348290, # andytimbo
	# 573609464620515351, # quaglet
}

s = aiohttp.ClientSession()

confirmed_emoji = '👍'

with open('roles.json', 'r') as f:
	roles = json.loads(f.read())

with open('doors.json', 'r') as f:
	doors = json.loads(f.read())

with open('tables.json', 'r') as f:
	tables = json.loads(f.read())

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

# def bot_channel(func, *args2, **kwargs2):
# 	print('2', args2, kwargs2)
# 	def wrapper(*args, **kwargs):
# 		print('1', args, kwargs)
# 		# print('Calling', func.__name__)
# 		message = args[0]
# 		if not message.guild or bot_channels[message.guild.id] == message.channel.id:
# 			return func(*args, **kwargs)
# 		else:
# 			print('no')
# 	return wrapper

@betterbot.command(name='e')
async def e(message):
	'Sends "e".'
	await message.send('e')

@betterbot.command(name='link')
async def link(message, ign: str=None):
	if not ign:
		return await message.send('Do `!link yourusername` to link to your Hypixel account.')
	ign = ign.strip()
	try:
		print('getting user data')
		# discord_name = await hypixel.get_discord_name(ign)
		data = await hypixel.get_user_data(ign)
		print('data')
		try:
			# discord_name = data['links']['DISCORD']
			discord_name = data['discord']['name']
			assert discord_name is not None
		except:
			raise hypixel.DiscordNotFound()
	except hypixel.PlayerNotFound:
		return await message.send('Invalid username.')
	except hypixel.DiscordNotFound:
		return await message.send("You haven't set your Discord username in Hypixel yet.")
	if str(message.author) == discord_name:
		pass # good
	else:
		return await message.send(embed=discord.Embed(
			description=f'Incorrect username. Did you link your account correctly in Hypixel? ({ign} is linked to {discord_name})'
		))

	old_rank = await db.get_hypixel_rank(message.author.id)
	new_rank = await hypixel.get_hypixel_rank(ign)

	# Give the user their rank in all servers
	for guild in client.guilds:
		member = guild.get_member(message.author.id)
		if not member:
			# Member isn't in the guild
			continue

		# Remove the user's old rank
		if old_rank:
			old_rank_role_id = get_role_id(guild.id, old_rank)
			if old_rank_role_id:
				old_rank_role = guild.get_role(old_rank_role_id)
				await member.remove_roles(old_rank_role, reason='Old rank')		
		
		new_rank = data['rank']
		new_rank_role_id = get_role_id(guild.id, new_rank)
		if new_rank_role_id:
			new_rank_role = guild.get_role(new_rank_role_id)
			await member.add_roles(new_rank_role, reason='Update rank')

	await db.set_hypixel_rank(message.author.id, new_rank)
	await db.set_minecraft_ign(message.author.id, ign, data['uuid'])

	if new_rank_role_id:
		await message.channel.send(
			embed=discord.Embed(
				description=f'Linked your account to **{ign}** and updated your role to **{new_rank}**.'
			)
		)
	else:
		await message.channel.send(
			embed=discord.Embed(
				description=f'Linked your account to **{ign}**.'
			)
		)

	# If you're muted, stop running the function
	mute_end = await db.get_mute_end(message.author.id)
	if (mute_end and mute_end > time.time()):
		return

	# You're already verified, stop running the function
	is_member = await db.get_is_member(message.author.id)
	if is_member: return

	for guild in client.guilds:
		member = guild.get_member(message.author.id)
		if not member:
			# Member isn't in the guild
			continue
		member_role_id = get_role_id(guild.id, 'member')
		member_role = guild.get_role(member_role_id)
		await member.add_roles(member_role, reason='New member linked')
	await db.set_is_member(message.author.id)

@betterbot.command(name='whois')
async def whois(message, member: Member=None):
	if not member:
		return await message.send('Do `!whois @member` to get information on that user.')
	data = await db.get_minecraft_data(member.id)
	if not data:
		return await message.send(embed=discord.Embed(
			description="This user hasn't linked their account yet. Tell them to do **!link**."
		))
	print(data)
	embed = discord.Embed(
		title=f'Who is {member}'
	)

	uuid = data['uuid']

	embed.add_field(
		name='IGN',
		value=data['ign'],
		inline=False,
	)
	embed.add_field(
		name='UUID',
		value=uuid,
		inline=False,
	)

	embed.set_thumbnail(url=f'https://crafatar.com/renders/head/{uuid}?overlay=1')

	await message.channel.send(embed=embed)


@betterbot.command(name='debugtime')
async def debugtime(message, length: Time):
	'Debugging command to test time'
	await message.send(seconds_to_string(length))

@betterbot.command(name='mute', bot_channel=False)
async def mute(message, member: Member, length: Time=0, reason: str=None):
	'Mutes a member for a specified amount of time'

	if not (
		has_role(message.author.id, 717904501692170260, 'helper')
		or has_role(message.author.id, 717904501692170260, 'trialhelper')
	): return

	if not member or not length:
		return await message.channel.send(
			'Invalid command usage. Example: **!mute gogourt 10 years nerd**'
		)

	if reason:
		reason = reason.strip()

	if reason:
		mute_message = f'<@{member.id}> has been muted for "**{reason}**".'
	else:
		mute_message = f'<@{member.id}> has been muted.'

	await message.send(embed=discord.Embed(
		description=mute_message
	))

	await db.add_infraction(
		member.id,
		'mute',
		reason
	)

	try:
		await member.send(f'You were muted for "**{reason}**"')
	except: pass

	try:
		await discordbot.mute_user(
			member,
			length,
			message.guild.id if message.guild else None
		)
	except discord.errors.Forbidden:
		await message.send("I don't have permission to do this")

@betterbot.command(name='unmute', bot_channel=False)
async def unmute(message, member: Member):
	'Removes a mute from a member'

	if not (
		has_role(message.author.id, 717904501692170260, 'helper')
		or has_role(message.author.id, 717904501692170260, 'trialhelper')
	): return

	await discordbot.unmute_user(
		member.id,
		reason=f'Unmuted by {str(message.author)}'
	)

	await message.send(embed=discord.Embed(
		description=f'<@{member.id}> has been unmuted.'
	))

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
	
	await discordbot.mute_user(
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
			await execute(command, locals())
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
	await discordbot.update_counter()

@betterbot.command(name='counting', aliases=['counter'])
async def get_counting(message, value):
	counter = await db.get_counter(message.guild.id)
	await message.channel.send(counter)

@betterbot.command(name='help', aliases=['commands'])
async def help_command(message):
	commands = [
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
		commands.extend([
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
		commands.extend([
			{
				'name': 'infractions',
				'args': '',
				'desc': 'View your own infractions (mutes, warns, etc)',
			}
		])

	description = []

	for command in commands:
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
	await message.channel.send(f'There are **{true_member_count:,}** people in this server.')

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

markov_ratelimit = {}

def check_markov_ratelimit(user):
	global markov_ratelimit
	if user not in markov_ratelimit: return False
	user_ratelimit = markov_ratelimit[user]
	last_minute_uses = 0
	last_20_second_uses = 0
	for ratelimit in user_ratelimit:
		if time.time() - ratelimit < 60:
			last_minute_uses += 1
			if time.time() - ratelimit < 20:
				last_20_second_uses += 1
		else:
			del user_ratelimit[0]
	if last_minute_uses >= 10: return True
	if last_20_second_uses > 2: return True
	return False

def add_markov_ratelimit(user):
	global markov_ratelimit
	if user not in markov_ratelimit:
		markov_ratelimit[user] = []
	markov_ratelimit[user].append(time.time())

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
		return await message.send('Unknown member. Example usage: **!rock piglegs**')

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

@betterbot.command(name='tictactoe', aliases=['ttt'], bot_channel=False)
async def tictactoe_command(message, player2: Member=None):
	if message.channel.id not in {
		720073985412562975, # gulag
		718076311150788649, # bot-commands
		719518839171186698, # staff-bot-commands
	} and message.guild: return
	is_gulag = message.channel.id == 720073985412562975

	ttt_game = tictactoe.Game()
	is_ai = True
	player1 = message.author

	title_msg = await message.send('**TIC TAC TOE**')
	board_msg = await message.send('(loading)')

	number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
	if is_gulag:
		number_emojis = list(reversed(number_emojis))
		random.shuffle(ttt_game.numbers)
		random.shuffle(number_emojis)

	for number_emoji in number_emojis:
		await board_msg.add_reaction(number_emoji)

	async def update_board():
		await board_msg.edit(content=ttt_game.render_board())
		await title_msg.edit(content=f'**TIC TAC TOE** (:{ttt_game.turn}:s turn)')

	await update_board()

	while True:
		# X
		if player1:
			placed = False
			while not placed:
				reaction, user = await client.wait_for('reaction_add', check=lambda reaction, user: user == player1 and reaction.emoji in number_emojis and reaction.message.id == board_msg.id)
				placing_spot = number_emojis.index(reaction.emoji)
				placed = ttt_game.board[placing_spot] is None
		else:
			await asyncio.sleep(1)
			placing_spot = ttt_game.ai_choose()
		print(placing_spot, ttt_game.turn)
		ttt_game.place(placing_spot)
		await update_board()
		try:
			await board_msg.clear_reaction(number_emojis[placing_spot])
		except discord.errors.Forbidden:
			await board_msg.remove_reaction(number_emojis[placing_spot], client.user)

		winner = ttt_game.check_win()
		if winner:
			break
		if None not in ttt_game.board:
			# tie
			break

		# O
		if player2:
			placed = False
			while not placed:
				reaction, user = await client.wait_for('reaction_add', check=lambda reaction, user: user == player2 and reaction.emoji in number_emojis and reaction.message.id == board_msg.id)
				placing_spot = number_emojis.index(reaction.emoji)
				placed = ttt_game.board[placing_spot] is None
		else:
			await asyncio.sleep(1)
			placing_spot = ttt_game.ai_choose()
		print(placing_spot, ttt_game.turn)
		ttt_game.place(placing_spot)
		await update_board()
		try:
			await board_msg.clear_reaction(number_emojis[placing_spot])
		except discord.errors.Forbidden:
			await board_msg.remove_reaction(number_emojis[placing_spot], client.user)

		winner = ttt_game.check_win()
		if winner:
			break
		if None not in ttt_game.board:
			# tie
			break
	if winner:
		await title_msg.edit(content=f'**TIC TAC TOE** (:{winner}: WINS)')
	else:
		await title_msg.edit(content='**TIC TAC TOE** (it\'s a tie)')

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

users_generating_shitpost = {}

@betterbot.command(name='shitpost', aliases=['markovshitpost'])
async def random_shitpost(message, title:str=''):
	if check_markov_ratelimit(message.author.id):
		return await message.send('Stop spamming the command, nerd')
	if users_generating_shitpost.get(message.author.id):
		return await message.send('Already generating shitpost')

	add_markov_ratelimit(message.author.id)

	users_generating_shitpost[message.author.id] = True

	if not title:
		title = await markovforums.generate_title()

	sent_message = await message.channel.send(embed=discord.Embed(
		title=title,
		description='loading...'
	))
	async for post_body in markovforums.generate_body(title):
		await sent_message.edit(embed=discord.Embed(
			title=title,
			description=post_body[:2000] + '...'
		))
	await sent_message.edit(embed=discord.Embed(
		title=title,
		description=post_body[:2000]
	))
	users_generating_shitpost[message.author.id] = False

@betterbot.command(name='bleach')
async def bleach(message):
	embed = discord.Embed(
		title="Here's a Clorox bleach if you want to unsee something weird:"
	)
	embed.set_image(url='https://cdn.discordapp.com/attachments/741200821936586785/741200842430087209/Icon_3.jpg')
	await message.channel.send(embed=embed)

@betterbot.command(name='jpeg')
async def jpegify_member(message, member: Member):
	async with message.channel.typing():
		img_size = 128
		user = client.get_user(member.id)
		with io.BytesIO() as output:
			asset = user.avatar_url_as(static_format='png', size=img_size)
			await asset.save(output)
			if '.gif' in asset._url:
				content_type = 'image/gif'
			else:
				content_type = 'image/png'
			output.seek(0)
			img_bytes = output.getvalue()
		
		url = await deepfry.upload(img_bytes, content_type)
	
	embed = discord.Embed(title='JPEG')

	embed.set_image(url=url)

	await message.channel.send(embed=embed)


@betterbot.command(name='wow')
async def wow(message):
	await message.author.send('https://im-a-puzzle.com/look_i_m_a_puzzle_4XZqEhin.puzzle')
	await message.delete()

rigged_duel_users = set()

@betterbot.command(name='rigduel', aliases=['rigduels'], bot_channel=False)
async def rig_duel_command(message):
	if message.author.id != 224588823898619905: return # only works for mat
	rigged_duel_users.add(message.author.id)
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
	if duel_at_zero:
		duel_winner = message.author
		duel_loser = opponent_1 if duel_winner == opponent_2 else opponent_2
		if duel_loser.id in rigged_duel_users:
			rigged_duel_users.remove(duel_loser.id)
			duel_winner_tmp = duel_winner
			duel_winner = duel_loser
			duel_loser = duel_winner_tmp
		await channel.send(f'<@{duel_winner.id}> won the duel!')
	else:
		duel_winner = opponent_1 if message.author == opponent_2 else opponent_2
		duel_loser = opponent_1 if duel_winner == opponent_2 else opponent_2
		if duel_loser.id in rigged_duel_users:
			rigged_duel_users.remove(duel_loser.id)
			duel_winner_tmp = duel_winner
			duel_winner = duel_loser
			duel_loser = duel_winner_tmp

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
		if not duel_statuses[duel_id]['ended']:
			await message.channel.send('5')
			await asyncio.sleep(1)
		if not duel_statuses[duel_id]['ended']:
			await message.channel.send('4')
			await asyncio.sleep(1)
		if not duel_statuses[duel_id]['ended']:
			await message.channel.send('3')
			await asyncio.sleep(1)
		if not duel_statuses[duel_id]['ended']:
			await message.channel.send('2')
			await asyncio.sleep(1)
		if not duel_statuses[duel_id]['ended']:
			await message.channel.send('1')
			await asyncio.sleep(1)
		if not duel_statuses[duel_id]['ended']:
			if random.randint(0, 9) == 0:
				await message.channel.send('sike')
				await asyncio.sleep(5)
			else:
				await message.channel.send('Shoot')
				duel_statuses[duel_id]['zero'] = True
				duel_statuses[duel_id]['ended'] = True
				if opponent.id == 719348452491919401:
					await message.channel.send(':gun:')
		else:
			duel_statuses[duel_id]['zero'] = True
		await asyncio.sleep(1)
	if message.author.id in active_duelers:
		active_duelers.remove(message.author.id)
	if opponent.id in active_duelers:
		active_duelers.remove(opponent.id)
		
@betterbot.command(name='ducksweirdclickbaitthing', aliases=['clickbait'])
async def ducksweirdclickbaitthing(message):
	await message.channel.send(ducksweirdclickbaitcommand.generate())

amongus_cooldown = {}
amongus_active = False

@betterbot.command(name='amongus', aliases=['votingsim', 'votingsimulator'], bot_channel=False)
async def amongus_command(message):
	global amongus_active
	if message.channel.id == 718076311150788649: # bot commands
		return await message.channel.send('This command only works in <#719579620931797002>')
	if message.channel.id != 719579620931797002: # general
		return
	if not (
		has_role(message.author.id, 717904501692170260, 'helper')
		or has_role(message.author.id, 717904501692170260, 'trialhelper')
		or has_role(message.author.id, 717904501692170260, 'sweat')
	):
		return await message.channel.send('You must be a sweat or staff member to start a game of Among Us')
	if amongus_active:
		return await message.channel.send('There is already a game of Among Us active')
	amongus_active = True
	players = []
	async for message in message.channel.history(limit=500):
		# make sure message has been created in past 15 minutes
		if message.created_at > datetime.now() - timedelta(minutes=15):
			# dont duplicate players
			if message.author not in players:
				players.append(message.author)
			# max of 8 players
			if len(players) >= 8:
				break
	if len(players) < 4:
		amongus_active = False
		return await message.channel.send('Chat is too dead right now :pensive:')
	await message.channel.send(embed=discord.Embed(title='the command doesnt work right now btw im just testing', description=str(players)))
	# return await message.channel.send('You must be a sweat or staff member to start a game of Among Us')
	




	# amongus_cooldown[message.author.id] = time.time()