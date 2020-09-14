from betterbot import BetterBot
import discord
import os
import json
import db
import time
import asyncio
import forums
from datetime import datetime, timedelta
import modbot
import markovforums

prefix = '!'
betterbot = BetterBot(
	prefix=prefix,
	bot_id=719348452491919401
)

with open('roles.json', 'r') as f:
	roles = json.loads(f.read())

def get_role_id(guild_id, role_name):
	return roles.get(str(guild_id), {}).get(role_name)

def has_role(member_id, guild_id, role_name):
	'Checks if a member has a role from roles.json'
	guild = client.get_guild(guild_id)
	member = guild.get_member(member_id)

	role_id = get_role_id(guild_id, role_name)
	return any([role_id == role.id for role in member.roles])

client = discord.Client()

async def start_bot():
	print('starting bot yeet')
	await client.start(os.getenv('token'))

@client.event
async def on_ready():
	print('ready')
	await forums.login(os.getenv('forumemail'), os.getenv('forumpassword'))

	await client.change_presence(
		activity=discord.Game(name='e')
	)
	active_mutes = await db.get_active_mutes()
	await markovforums.init()
	print('active_mutes', active_mutes)
	for muted_id in active_mutes:
		asyncio.ensure_future(unmute_user(muted_id, True))

@client.event
async def on_member_join(member):
	# if datetime.now() - member.created_at < timedelta(days=7):
	# 	await member.send('You were kicked from Forum Sweats because your Discord account is too new. This is an anti-spam measure, and you will be able to join the server after your account is at least week old.')
	# 	await member.kick(reason='Account too new')
	# 	return
	mute_end = await db.get_mute_end(member.id)
	if mute_end and mute_end > time.time():
		await mute_user(member, mute_end - time.time(), member.guild.id)
		await asyncio.sleep(1)
		member_role_id = get_role_id(member.guild.id, 'member')
		member_role = member.guild.get_role(member_role_id)
		await member.remove_roles(member_role, reason='mee6 cringe')
	else:
		is_member = await db.get_is_member(member.id)

		member_role_id = get_role_id(member.guild.id, 'member')
		member_role = member.guild.get_role(member_role_id)
	
		if is_member:
			await member.add_roles(member_role, reason='Linked member rejoined')
		else:
			if datetime.now() - member.created_at > timedelta(days=365):
				await member.add_roles(member_role, reason='Account is older than a year')
			else:
				await member.send('Hello! Please verify your Minecraft account by doing !link <your username>. (You must set your Discord in your Hypixel settings)')

def is_close_to_everyone(name):
	return name and name.lower().strip('@').split()[0] == 'everyone'


@client.event
async def on_member_update(before, after):
	# nick update
	wacky_characters = ['𒈙', 'ٴٴ,', '˞˞˞˞˞˞˞˞˞˞˞˞˞˞˞˞˞˞T']
	if after.nick:
		if any([c in after.nick or '' for c in wacky_characters]):
			return await after.edit(nick=before.nick)
	else:
		if any([c in after.display_name or '' for c in wacky_characters]):
			return await after.edit(nick='i am a poopoo head')
	if is_close_to_everyone(after.nick):
		if not is_close_to_everyone(before.nick):
			return await after.edit(nick=before.nick)
		elif not is_close_to_everyone(after.name):
			return await after.edit(nick=after.name)
		else:
			return await after.edit(nick='i am a poopoo head')

	await asyncio.sleep(5)
	after = after.guild.get_member(after.id)

	# role update
	# if before.roles != after.roles:
	# 	muted_role = after.guild.get_role(719354039778803813)
	# 	member_role = after.guild.get_role(718090644148584518)
	# 	if muted_role in after.roles and member_role in after.roles:
	# 		await after.remove_roles(member_role, reason='Member manually muted')
	# 		print('manual mute')
	# 		asyncio.ensure_future(mute_user(after, 60 * 60 * 24))
	# 	elif muted_role in before.roles and muted_role not in after.roles and member_role not in after.roles:
	# 		print('manual unmute')
	# 		await after.add_roles(member_role, reason='Member manually unmuted')
	# 		await unmute_user(after.id, wait=False)
	

most_recent_counting_message_id = None

async def update_counter():
	# current_counter = await db.get_counter(717904501692170260)
	# print('updated counter to', current_counter)
	# counting_channel = client.get_channel(738449805218676737)
	# await counting_channel.edit(name=f'counting-{current_counter}', reason='Counting channel')
	# print('ok')
	return

async def process_counting_channel(message):
	global most_recent_counting_message_id
	if message.channel.id != 738449805218676737:
		# if the message wasn't in the counting channel, you can ignore all of this
		return
	if message.author.id == 719348452491919401:
		# if the message was sent by forum sweats, ignore it
		return
	old_number = await db.get_counter(message.guild.id)
	content = message.content.replace(',', '')
	try:
		new_number = float(content)
	except:
		new_number = 0
	if old_number == 0 and new_number != 1:
		await message.delete()
		await message.channel.send(f'<@{message.author.id}>, please start at 1', delete_after=10)
	elif new_number == old_number + 1:
		await db.set_counter(message.guild.id, int(new_number))
		most_recent_counting_message_id = message.id
	else:
		await db.set_counter(message.guild.id, 0)
		await message.channel.send(f"<@{message.author.id}> put an invalid number and ruined it for everyone. (Ended at {old_number})")
		asyncio.ensure_future(mute_user(message.author, 60 * 60))
	await update_counter()
	

@client.event
async def on_message(message):
	# skyblock-updates
	if message.channel.id == 738937428378779659:
		await message.publish()
	if message.channel.id == 719570596005937152: # spam
		if message.content and message.content[0] != '!' and not message.author.bot:
			uwuized_message = message.content\
				.replace('@', '')\
				.replace('r', 'w')\
				.replace('l', 'w')\
				.replace('R', 'W')\
				.replace('L', 'W')
			await message.channel.send(uwuized_message)
	asyncio.ensure_future(db.add_message(message.author.id))
	await process_counting_channel(message)
	await betterbot.process_commands(message)
	await modbot.process_messsage(message)

@client.event
async def on_message_delete(message):
	print('deleted:', message.author, message.content)
	if message.id == most_recent_counting_message_id:
		counter = await db.get_counter(message.guild.id)
		await message.channel.send(str(counter))

@client.event
async def on_message_edit(before, after):
	if after.channel.id == 738449805218676737:
		await after.delete()
	await modbot.process_messsage(after, warn=False)

async def mute_user(member, length, guild_id=None):
	guild_id = guild_id if guild_id else 717904501692170260
	guild = client.get_guild(guild_id)

	muted_role_id = get_role_id(guild_id, 'muted')
	muted_role = guild.get_role(muted_role_id)

	member_role_id = get_role_id(guild_id, 'member')
	member_role = guild.get_role(member_role_id)

	sweat_role_id = get_role_id(guild_id, 'sweat')
	sweat_role = guild.get_role(sweat_role_id)

	print(sweat_role, 'sweat_role')

	og_role_id = get_role_id(guild_id, 'og')
	og_role = guild.get_role(og_role_id)

	# if length == 0:
	# 	await message.send(str(length))

	print('muted_role', muted_role)

	print()

	await member.add_roles(muted_role)
	await member.remove_roles(member_role)
	
	unmute_time = await db.get_mute_end(member.id)
	unmute_in = unmute_time - time.time()

	muted_before = False
	
	if unmute_in < 0:
		extra_data = {
			'sweat': sweat_role in member.roles,
			'og': og_role in member.roles,
		}
	else:
		extra_data = await db.get_mute_data(member.id)
		muted_before = True

	await db.set_mute_end(
		member.id,
		time.time() + length,
		extra_data
	)

	if sweat_role in member.roles:
		await member.remove_roles(sweat_role)

	if og_role in member.roles:
		await member.remove_roles(og_role)

	gulag = client.get_channel(720073985412562975)
	if not muted_before:
		await gulag.send(f'Welcome to gulag, <@{member.id}>.')
	else:
		mute_remaining = int(length)
		mute_remaining_minutes = int(mute_remaining // 60)
		mute_remaining_hours = int(mute_remaining_minutes // 60)
		if mute_remaining_hours >= 2:
			mute_str = f'{mute_remaining_hours} hours'
		elif mute_remaining_hours == 1:
			mute_str = f'one hour'
		elif mute_remaining_minutes >= 2:
			mute_str = f'{mute_remaining_minutes} minutes'
		elif mute_remaining_minutes == 1:
			mute_str = f'one minute'
		elif mute_remaining == 1:
			mute_str = f'one second'
		else:
			mute_str = f'{mute_remaining} seconds'

		await gulag.send(f'<@{member.id}>, your mute is now {mute_str}')

	await unmute_user(member.id, wait=True)

async def unmute_user(user_id, wait=False, gulag_message=True, reason=None):
	'Unmutes a user after a certain amount of seconds pass'
	if wait:
		print('unmuting in...')
		unmute_time = await db.get_mute_end(user_id)
		unmute_in = unmute_time - time.time()
		print('unmute_in', unmute_in)
		await asyncio.sleep(unmute_in)
		if (await db.get_mute_end(user_id) != unmute_time):
			return print('Mute seems to have been extended.')
	print('now unmuting')

	mute_data = await db.get_mute_data(user_id)

	for guild in client.guilds:
		member = guild.get_member(user_id)
		if not member: continue

		muted_role_id = get_role_id(guild.id, 'muted')
		muted_role = guild.get_role(muted_role_id)

		member_role_id = get_role_id(guild.id, 'member')
		member_role = guild.get_role(member_role_id)

		await member.add_roles(member_role, reason=reason)
		await member.remove_roles(muted_role, reason=reason)

		sweat_role_id = get_role_id(guild.id, 'sweat')
		sweat_role = guild.get_role(sweat_role_id)

		og_role_id = get_role_id(guild.id, 'og')
		og_role = guild.get_role(og_role_id)

		if mute_data.get('sweat'):
			await member.add_roles(sweat_role)

		if mute_data.get('og'):
			await member.add_roles(og_role)


	await db.set_mute_end(user_id, time.time())

	if gulag_message:
		gulag = client.get_channel(720073985412562975)
		await gulag.send(f'<@{user_id}> has left gulag.')



	# await member.send(embed=discord.Embed(
	# 	description='You have been unmuted.'
	# ))

@client.event
async def on_raw_reaction_add(payload):
	# ignore reactions from mat
	if payload.user_id == 224588823898619905:
		return
	if payload.message_id == 732551899374551171:
		if str(payload.emoji.name).lower() != 'disagree':
			message = await client.get_channel(720258155900305488).fetch_message(732551899374551171)
			print('removed reaction')
			await message.clear_reaction(payload.emoji)

		if payload.message_id not in {732552573806051328, 732552579531407422}: return
		message = await client.get_channel(720258155900305488).fetch_message(payload.message_id)
		await message.clear_reaction(payload.emoji)
	if payload.message_id == 741806331484438549:
		if str(payload.emoji.name).lower() != 'disagree':
			message = await client.get_channel(720258155900305488).fetch_message(741806331484438549)
			await message.remove_reaction(payload.emoji, payload.member)
			print('removed reaction!')
	# if payload.message_id == wynncraft: # wynncraft role
		


def api_get_members():
	guild_id = 717904501692170260
	guild = client.get_guild(guild_id)

	total_member_count = guild.member_count

	owner_role_id = 717906079572295750
	coowner_role_id = 717906242026340373
	admin_role_id = 740985921389723709
	mod_role_id = get_role_id(guild_id, 'mod')
	helper_role_id = get_role_id(guild_id, 'helper')
	party_planner_role_id = 733695759425208401

	owner_role = guild.get_role(owner_role_id)
	coowner_role = guild.get_role(coowner_role_id)
	admin_role = guild.get_role(admin_role_id)
	mod_role = guild.get_role(mod_role_id)
	helper_role = guild.get_role(helper_role_id)
	party_planner_role = guild.get_role(party_planner_role_id)

	owner_list = []
	coowner_list = []
	admin_list = []
	mod_list = []
	helper_list = []
	party_planner_list = []

	for member in guild.members:
		if owner_role in member.roles:
			owner_list.append(member.name)
		elif coowner_role in member.roles:
			coowner_list.append(member.name)
		elif admin_role in member.roles:
			admin_list.append(member.name)
		elif mod_role in member.roles:
			mod_list.append(member.name)
		elif helper_role in member.roles:
			helper_list.append(member.name)
		elif party_planner_role in member.roles:
			party_planner_list.append(member.name)

	return {
		'member_count': total_member_count,
		'roles': {
			'owner': ', '.join(owner_list),
			'coowner': ', '.join(coowner_list),
			'admin': ', '.join(admin_list),
			'mod': ', '.join(mod_list),
			'helper': ', '.join(helper_list),
			'party_planner': ', '.join(party_planner_list),
		}
	}