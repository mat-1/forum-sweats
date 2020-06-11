from betterbot import BetterBot
import discord
import os
import json
import db
import time
import asyncio

prefix = '!'
betterbot = BetterBot(
	prefix=prefix,
	bot_id=719348452491919401
)

with open('roles.json', 'r') as f:
	roles = json.loads(f.read())

def get_role_id(guild_id, rank_name):
	return roles.get(str(guild_id), {}).get(rank_name)

client = discord.Client()

async def start_bot():
	print('starting bot yeet')
	await client.start(os.getenv('token'))

@client.event
async def on_ready():
	print('ready')
	await client.change_presence(
		activity=discord.Game(name='e')
	)
	active_mutes = await db.get_active_mutes()
	for muted_id in active_mutes:
		mute_end = active_mutes[muted_id]
		await unmute_user(muted_id, mute_end)

@client.event
async def on_member_join(member):
	mute_end = await db.get_mute_end(member.id)
	if mute_end and mute_end > time.time():
		await mute_user(member, time.time() - mute_end, member.guild.id)

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
	await db.set_mute_end(
		member.id,
		time.time() + length,
		{
			'sweat': sweat_role in member.roles,
			'og': og_role in member.roles,
		}
	)

	if sweat_role in member.roles:
		await member.remove_roles(sweat_role)

	if og_role in member.roles:
		await member.remove_roles(og_role)



	await unmute_user(member.id, length)

async def unmute_user(user_id, unmute_in=0):
	'Unmutes a user after a certain amount of seconds pass'
	if unmute_in > 0:
		await asyncio.sleep(unmute_in)

	mute_data = await db.get_mute_data(user_id)

	for guild in client.guilds:
		member = guild.get_member(user_id)

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


	await db.set_mute_end(member.id, time.time())

	

	# await member.send(embed=discord.Embed(
	# 	description='You have been unmuted.'
	# ))
