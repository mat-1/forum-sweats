import discord
from discordbot import betterbot, client
import discordbot
from discord.ext import commands
import hypixel
import db
from betterbot import (
	Member,
	Time
)
import json
from datetime import datetime
import io
from contextlib import redirect_stdout, redirect_stderr
import forums

bot_owners = {
	224588823898619905, # mat
	385506886222348290, # andytimbo
	573609464620515351, # quaglet
}

with open('roles.json', 'r') as f:
	roles = json.loads(f.read())


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

	# Remove the user's old rank
	old_rank = await db.get_hypixel_rank(message.author.id)
	if old_rank:
		old_rank_role_id = get_role_id(message.guild.id, old_rank)
		if old_rank_role_id:
			old_rank_role = message.guild.get_role(old_rank_role_id)
			await message.author.remove_roles(old_rank_role, reason='Old rank')
	
	# new_rank = await hypixel.get_hypixel_rank(ign)
	new_rank = data['rank']
	new_rank_role_id = get_role_id(message.guild.id, new_rank)
	if new_rank_role_id:
		new_rank_role = message.guild.get_role(new_rank_role_id)
		await message.author.add_roles(new_rank_role, reason='Update rank')

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
	await message.send(str(length))

@betterbot.command(name='mute', bot_channel=False)
async def mute(message, member: Member, length: Time=0, reason: str=None):
	'Mutes a member for a specified amount of time'

	if not message.author.permissions_in(message.channel).manage_messages: return

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

	if not message.author.permissions_in(message.channel).manage_messages: return

	await discordbot.unmute_user(
		member.id
	)

	await message.send(embed=discord.Embed(
		description=f'<@{member.id}> has been unmuted.'
	))

@betterbot.command(name='infractions', bot_channel=False)
async def infractions(message, member: Member=None):
	'Checks the infractions that a user has (mutes, warns, bans, etc)'

	if not member:
		member = message.author

	is_checking_self = message.author.id == member.id

	if not is_checking_self and not message.author.permissions_in(message.channel).manage_messages:
		return

	infractions = await db.get_infractions(member.id)

	embed_title = 'Your infractions' if is_checking_self else f'{member}\'s infractions'

	embed = discord.Embed(
		title=embed_title
	)
	for infraction in infractions:
		value = infraction.get('reason') or '<no reason>'
		name = infraction['type']
		if 'date' in infraction:
			date_pretty = infraction['date'].strftime('%m/%d/%Y')
			name += f' ({date_pretty})'
		embed.add_field(
			name=name,
			value=value,
			inline=False
		)

	if len(infractions) == 0:
		embed.description = 'No infractions'

	if is_checking_self:
		await message.author.send(embed=embed)
	else:
		await message.send(embed=embed)


@betterbot.command(name='clearinfractions', bot_channel=False)
async def clearinfractions(message, member: Member, date: str=None):
	'Checks the infractions that a user has (mutes, warns, bans, etc)'

	if not message.author.permissions_in(message.channel).manage_messages:
		return

	if not member or not date:
		return await message.send('Please use `!clearinfractions @member date`')
	# month, day, year = date.split('/')
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
	f2 = io.StringIO()
	with redirect_stdout(f):
		command = message.content.split(None, 1)[1].strip()
		if command.startswith('```') and command.endswith('```'):
			command = '\n'.join(command.split('\n')[1:])
			command = command[:-3]
		await execute(command, locals())
	out = f.getvalue()
	if out == '':
		out = 'No output.'
	await message.send(
		embed=discord.Embed(
			title='Eval',
			description=out
		)
	)

@betterbot.command(name='help', aliases=['commands'])
async def help_command(message, code: str):
	commands = []

# !forum
@betterbot.command(name='forum', aliases=['forums', 'f'])
async def forum(message):
	await message.send('Forum commands: **!forums user (username)**')

# # !forum user
@betterbot.command(name='forum', aliases=['forums', 'f'])
async def forum_user(message, command, user):
	if command not in {
		'member',
		'user'
	}:
		raise TypeError
	
	await 
