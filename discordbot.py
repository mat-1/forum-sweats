from betterbot import BetterBot
import discord
import os
import json
import db
import time
import asyncio
import forums
from datetime import datetime, timedelta

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
	print('active_mutes', active_mutes)
	for muted_id in active_mutes:
		asyncio.ensure_future(unmute_user(muted_id, True))

@client.event
async def on_member_join(member):
	if datetime.now() - member.created_at < timedelta(days=7):
		await member.send('You were kicked from Forum Sweats because your Discord account is too new. This is an anti-spam measure, and you will be able to join the server after your account is at least week old.')
		await member.kick(reason='Account too new')
		return
	mute_end = await db.get_mute_end(member.id)
	if mute_end and mute_end > time.time():
		await mute_user(member, mute_end - time.time(), member.guild.id)
	else:
		is_member = await db.get_is_member(member.id)
		if is_member:
			member_role_id = get_role_id(member.guild.id, 'member')
			member_role = member.guild.get_role(member_role_id)
			await member.add_roles(member_role, reason='Linked member rejoined')

@client.event
async def on_message(message):
	await betterbot.process_commands(message)

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

async def unmute_user(user_id, wait=False, gulag_message=True):
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

		await member.add_roles(member_role)
		await member.remove_roles(muted_role)

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
