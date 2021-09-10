from . import commands as commands_module
from .commandparser import CommandParser
from typing import Any, List, Union
from datetime import datetime
from . import uwuify
from . import modbot
from . import w2n
from . import db
import importlib
import discord
import asyncio
import forums
import base64
import config
import time
import math
import os

commands: Any = commands_module

intents = discord.Intents.default()
intents.members = True
intents.presences = True


token = os.getenv('token')
is_dev = os.getenv('dev', 'false').lower() == 'true'
commandparser = CommandParser(
	prefix=config.prefix,
	bot_id=int(base64.b64decode(token.split('.')[0])) if token else 0
)


def get_role_id(guild_id, role_name):
	return config.roles.get(role_name)


def has_role(member_id: int, role_name: str, guild_id=None):
	'Checks if a member has a role from roles.json'
	if is_dev:
		return True
	if not guild_id:
		guild_id = config.main_guild
	guild = client.get_guild(guild_id)
	member = guild.get_member(member_id)

	role_id = get_role_id(guild_id, role_name)
	return any([role_id == role.id for role in member.roles])


client = discord.Client(intents=intents)


# this has to be here for there to not be an error
from . import starboard


async def start_bot():
	print('starting bot pog')
	await client.start(token)

cached_invites = []


async def check_dead_chat():
	global is_chat_dead
	guild = client.get_guild(config.main_guild)
	general_channel = guild.get_channel(config.channels['general'])
	while True:
		await asyncio.sleep(5)
		time_since_message = time.time() - last_general_message
		if time_since_message > 60 * 15 and not is_chat_dead:
			await general_channel.send('dead chat xD')
			is_chat_dead = True


async def give_hourly_bobux():
	while True:
		time_until_bobux_given = 3600 - ((time.time()) % 3600)
		await asyncio.sleep(time_until_bobux_given)
		members = await db.get_active_members_from_past_hour(1)
		for member_data in members:
			member_id = member_data['discord']
			messages_in_past_hour = member_data['hourly_messages']
			given_bobux = 0
			if messages_in_past_hour >= 20:
				given_bobux += 10
			elif messages_in_past_hour >= 10:
				given_bobux += 5
			elif messages_in_past_hour >= 1:
				given_bobux += 1
			await db.change_bobux(member_id, given_bobux, is_activity_bobux=True)
			await check_bobux_roles(member_id)


async def renew_sub(sub):
	tier = sub['tier']
	tier_cost = commands.sub.tiers[tier]

	bobux = await db.get_bobux(sub['sender'])

	guild_id = config.main_guild

	guild = client.get_guild(guild_id)

	sender_member = guild.get_member(sub['sender'])
	receiver_member = guild.get_member(sub['id'])

	if tier_cost > bobux:
		# too expensive :pensive:
		await commands.unsub.unsubscribe(sub['sender'], sub['id'])
		try:
			await sender_member.send(embed=discord.Embed(
				description=(
					f'You don\'t have enough bobux to continue your sub to {receiver_member.mention}, '
					'so your subscription has been cancelled.'
				)
			))
			return
		except:
			pass
	else:
		# this will also take and give bobux accordingly
		await commands.sub.subscribe(sub['sender'], sub['id'], tier)


async def queue_renew_sub(sub):
	next_payment_delta = sub['next_payment'] - discord.utils.utcnow()
	await asyncio.sleep(next_payment_delta.total_seconds())
	await renew_sub(sub)


async def give_subbed_bobux():
	subs = await db.bobux_get_all_subscriptions()
	tasks = []
	for sub in subs:
		if sub['owed']:
			print('renewing sub', sub['id'], sub['sender'])
			await renew_sub(sub)
		else:
			tasks.append(queue_renew_sub(sub))

	if tasks:
		await asyncio.gather(*tasks)


async def give_active_mutes():
	active_mutes = await db.get_active_mutes()
	for muted_id in active_mutes:
		asyncio.ensure_future(unmute_user(muted_id, True))

already_ready = False

@client.event
async def on_ready():
	global cached_invites, already_ready
	print('ready')
	if already_ready: return
	already_ready = True
	try:
		await forums.login(os.getenv('forumemail'), os.getenv('forumpassword'))
	except: pass

	for module in command_modules:
		if hasattr(module, 'init'):
			asyncio.ensure_future(module.init(), loop=client.loop)

	# await client.change_presence(
	# 	activity=discord.Game(name='your mom')
	# )

	# send a message in #counting saying the current number if people messed up counting while it was down
	try:
		current_number = await db.get_counter(config.main_guild)
		counting_channel = client.get_channel(config.channels['counting'])
		most_recent_counting_message = (await counting_channel.history(limit=1).flatten())[0]
		try:
			most_recent_number = w2n.word_to_num(most_recent_counting_message.content)
		except:
			most_recent_number = -1
		did_bot_confirm_most_recent = False
		if most_recent_counting_message.author.id == client.user.id:
			did_bot_confirm_most_recent = True
		for reaction in most_recent_counting_message.reactions:
			if str(reaction.emoji) == str(COUNTING_CONFIRMATION_EMOJI):
				async for user in reaction.users():
					if user.id == client.user.id:
						did_bot_confirm_most_recent = True
						break
			if did_bot_confirm_most_recent:
				break
		if most_recent_number != current_number or not did_bot_confirm_most_recent:
			await counting_channel.send(f'{current_number}')
	except Exception as e:
		print(type(e), e)

	if not is_dev:
		try:
			guild = client.get_guild(config.main_guild)
			cached_invites = await guild.invites()
		except:
			print('Failed getting guild invites, make sure the config is correct.')

		asyncio.ensure_future(check_dead_chat(), loop=client.loop)
		asyncio.ensure_future(give_active_mutes(), loop=client.loop)
		asyncio.ensure_future(give_hourly_bobux(), loop=client.loop)
		asyncio.ensure_future(give_subbed_bobux(), loop=client.loop)
	
	from forumsweats.commands.giveaway import continue_giveaways
	asyncio.ensure_future(continue_giveaways(), loop=client.loop)


@client.event
async def on_member_join(member):
	if is_dev: return
	global cached_invites
	cached_invites_dict = {invite.code: invite for invite in cached_invites}
	guild = client.get_guild(config.main_guild)
	new_invites = await guild.invites()
	used_invite = None
	for invite in new_invites:
		if invite.code in cached_invites_dict:
			invite_uses_before = cached_invites_dict[invite.code].uses
		else:
			invite_uses_before = 0
		invite_uses_now = invite.uses
		if invite_uses_now > invite_uses_before:
			used_invite = invite

	try:
		bot_logs_channel = client.get_channel(718107452960145519)
		if used_invite:
			await bot_logs_channel.send(embed=discord.Embed(
				description=f'<@{member.id}> joined using discord.gg/{used_invite.code} (created by <@{used_invite.inviter.id}>, {used_invite.uses} uses)'
			))
		else:
			await bot_logs_channel.send(embed=discord.Embed(
				description=f'<@{member.id}> joined using an unknown invite'
			))
	except:
		# if theres an error, the channel probably just doesnt exist
		pass

	cached_invites = await guild.invites()

	if 'ban speedrun' in member.name.lower() or 'forum sweats nsfw' in member.name.lower():
		return await member.ban(reason='has blacklisted phrase in name')

	if used_invite:
		await db.add_invited_member(used_invite.inviter.id, member.id)
		from .commands.promoter import check_promoter
		asyncio.ensure_future(check_promoter(member, None, False))

	moot_end = await db.get_mooted_end(member.id)
	is_mooted = moot_end and moot_end > time.time()
	if is_mooted:
		moot_remaining = moot_end - time.time()
		await moot_user(member, moot_remaining, member.guild.id, gulag_message=False)

	mute_end = await db.get_mute_end(member.id)
	is_muted = mute_end and mute_end > time.time()
	if is_muted:
		mute_remaining = mute_end - time.time()
		await mute_user(member, mute_remaining, member.guild.id, gulag_message=False)
		await asyncio.sleep(1)
		member_role_id = get_role_id(member.guild.id, 'member')
		member_role = member.guild.get_role(member_role_id)
		await member.remove_roles(member_role, reason='mee6 cringe')
	else:

		member_role_id = get_role_id(member.guild.id, 'member')
		member_role = member.guild.get_role(member_role_id)

		await member.add_roles(member_role, reason='Member joined')


def is_close_to_everyone(name):
	return name and name.lower().strip('@').split()[0] in ['everyone', 'here']


@client.event
async def on_member_update(before, after):
	# nick update
	wacky_characters = ['𒈙', 'ٴٴ', '˞˞˞˞˞˞˞˞˞˞˞˞˞˞˞˞˞˞T', '﷽', '𒐪']
	if after.nick:
		if any([c in after.nick or '' for c in wacky_characters]):
			return await after.edit(nick=before.nick)
	else:
		if any([c in after.display_name or '' for c in wacky_characters]):
			return await after.edit(nick='i am a poopoo head ' + str(after.id)[-5:])
	if is_close_to_everyone(after.nick):
		if not is_close_to_everyone(before.nick):
			return await after.edit(nick=before.nick)
		elif not is_close_to_everyone(after.name):
			return await after.edit(nick=after.name)
		else:
			return await after.edit(nick='i am a poopoo head ' + str(after.id)[-5:])

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
most_recent_infinite_counting_message_id = None

# a dict of ids to the last time a member sent a message in #counting
counting_cooldowns = {}

COUNTING_CONFIRMATION_EMOJI = '✅'

async def process_counting_channel(message):
	global most_recent_counting_message_id
	if message.channel.id != config.channels.get('counting'):
		# if the message wasn't in the counting channel, you can ignore all of this
		return
	elif message.author.bot:
		# if the message was sent by forum sweats, ignore it
		return
	# the message is too long
	elif len(message.content) > 200:
		await message.delete()
		return

	if (
		message.author.id in counting_cooldowns
		and counting_cooldowns[message.author.id] + message.channel.slowmode_delay > time.time()
	):
		# delete messages if the author hasn't waited the full cooldown
		return await message.delete()


	old_number = await db.get_counter(message.guild.id)
	try:
		new_number = w2n.word_to_num(message.content)
	except ValueError:
		new_number = 0
	if old_number == 0 and new_number != 1:
		await message.delete()
		await message.channel.send(f'<@{message.author.id}>, please start at 1', delete_after=10)
	elif new_number == old_number + 1:
		try:
			await message.add_reaction(COUNTING_CONFIRMATION_EMOJI)
		except:
			# if there was an error adding the reaction, just delete the message
			return await message.delete()
		await db.set_counter(message.guild.id, int(new_number))
		most_recent_counting_message_id = message.id

		# how much bobux should be given for counting
		counting_bobux = math.ceil(new_number / 10)
		# give bobux every time you count
		await db.change_bobux(message.author.id, counting_bobux)
		# we do a try except in case the user blocked the bot
	else:
		if has_role(message.author.id, 'helper'):
			# if the user has the helper role and they mess up counting, delete their message
			return await message.delete()
		await db.set_counter(message.guild.id, 0)
		await message.channel.send(
			f"<@{message.author.id}> put an invalid number and ruined it for everyone. (Ended at {old_number})"
		)
		asyncio.ensure_future(mute_user(message.author, 60 * 60))
	counting_cooldowns[message.author.id] = time.time()

async def process_infinite_counting_channel(message):
	global most_recent_infinite_counting_message_id
	if message.channel.id != config.channels.get('infinite-counting'):
		# if the message wasn't in the counting channel, you can ignore all of this
		return
	elif message.author.bot:
		# if the message was sent by forum sweats, ignore it
		return
	# the message is too long
	elif len(message.content) > 200:
		await message.delete()
		return

	old_number = await db.get_infinite_counter(message.guild.id)
	last_person_to_count = await db.get_last_person_in_infinite_counting(message.guild.id)

	# the same person can't count twice in a row in #infinite-counting
	if last_person_to_count == message.author.id:
		return await message.delete()

	try:
		new_number = w2n.word_to_num(message.content)
	except:
		new_number = 0
	if old_number == 0 and new_number != 1:
		await message.delete()
		await message.channel.send(f'<@{message.author.id}>, please start at 1', delete_after=10)
	elif new_number == old_number + 1:
		try:
			await message.add_reaction(COUNTING_CONFIRMATION_EMOJI)
		except:
			# if there was an error adding the reaction, just delete the message
			return await message.delete()
		most_recent_infinite_counting_message_id = message.id
		await db.set_infinite_counter(message.guild.id, int(new_number))
		await db.set_last_person_in_infinite_counting(message.guild.id, message.author.id)
	else:
		await message.delete()

last_general_message = time.time()
is_chat_dead = False


async def process_suggestion(message):
	if message.type == discord.MessageType.thread_created:
		return await message.delete()
	agree_emoji = client.get_emoji(719235230958878822)
	disagree_emoji = client.get_emoji(719235358029512814)
	await message.add_reaction(agree_emoji)
	await message.add_reaction(disagree_emoji)


@client.event
async def on_message(message: discord.Message):
	global last_general_message
	global is_chat_dead

	if message.channel.id == config.channels.get('skyblock-updates'):  # skyblock-updates
		await message.publish()
	if message.channel.id == config.channels.get('general'):  # general
		last_general_message = time.time()
		if not message.author.bot:
			is_chat_dead = False
	if message.channel.id == config.channels.get('suggestions'):  # suggestions
		await process_suggestion(message)
	if message.channel.id == config.channels.get('spam'):  # spam
		if message.content and message.content[0] != '!' and not message.author.bot:
			uwuized_message = uwuify.uwuify(message.content, limit=2000)
			await message.channel.send(uwuized_message)
	if message.channel.id == config.channels.get('giveaway'):
		# delete pin messages created by the bot in giveaways
		if message.type == discord.MessageType.pins_add and message.author.id == client.user.id:
			await message.delete()

	asyncio.ensure_future(db.add_message(message.author.id))
	await process_counting_channel(message)
	await process_infinite_counting_channel(message)
	await commandparser.process_commands(message)
	await modbot.process_messsage(message)


@client.event
async def on_message_delete(message):
	print('deleted:', message.author, message.content)
	if message.id == most_recent_counting_message_id:
		counter = await db.get_counter(message.guild.id)
		await message.channel.send(str(counter))
	elif message.id == most_recent_infinite_counting_message_id:
		counter = await db.get_infinite_counter(message.guild.id)
		await message.channel.send(str(counter))


@client.event
async def on_message_edit(before, after):
	if (
		after.channel.id == config.channels.get('counting')
		or after.channel.id == config.channels.get('infinite-counting')
	):
		await after.delete()
	await modbot.process_messsage(after, warn=False)


async def mute_user(member, length, guild_id=None, gulag_message=True, rock_immune=False, replace=True):
	if not replace:
		current_mute_length = time.time() - await db.get_mute_end(member.id)
		if length < current_mute_length:
			return


	guild_id = guild_id if guild_id else config.main_guild
	guild = client.get_guild(guild_id)

	muted_role_id = get_role_id(guild_id, 'muted')
	muted_role = guild.get_role(muted_role_id)

	if not muted_role: return print('muted role not found')

	member_role_id = get_role_id(guild_id, 'member')
	member_role = guild.get_role(member_role_id)

	sweat_role_id = get_role_id(guild_id, 'sweat')
	sweat_role = guild.get_role(sweat_role_id)

	og_role_id = get_role_id(guild_id, 'og')
	og_role = guild.get_role(og_role_id)

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
	await db.set_rock_immune(member.id, rock_immune)

	if sweat_role in member.roles:
		await member.remove_roles(sweat_role)

	if og_role in member.roles:
		await member.remove_roles(og_role)

	gulag = client.get_channel(config.channels['gulag'])
	if gulag_message and gulag:
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
		unmute_time = await db.get_mute_end(user_id)
		unmute_in = unmute_time - time.time()
		await asyncio.sleep(unmute_in)
		if (await db.get_mute_end(user_id) != unmute_time):
			return

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
		gulag = client.get_channel(config.channels['gulag'])
		if gulag:
			await gulag.send(f'<@{user_id}> has left gulag.')

	# await member.send(embed=discord.Embed(
	# 	description='You have been unmuted.'
	# ))


async def moot_user(member, length, guild_id=None, gulag_message=True):
	guild_id = guild_id if guild_id else config.main_guild
	guild = client.get_guild(guild_id)

	mooted_role_id = get_role_id(guild_id, 'mooted')
	mooted_role = guild.get_role(mooted_role_id)

	if not mooted_role: return

	await member.add_roles(mooted_role)

	unmoot_time = await db.get_mooted_end(member.id)
	unmoot_in = unmoot_time - time.time()

	if unmoot_in < 0:
		extra_data = {}
	else:
		extra_data = await db.get_moot_data(member.id)

	await db.set_moot_end(
		member.id,
		time.time() + length,
		extra_data
	)


	await unmoot_user(member.id, wait=True)


async def unmoot_user(user_id, wait=False, gulag_message=True, reason=None):
	'Unmoots a user after a certain amount of seconds pass'
	if wait:
		unmoot_time = await db.get_mooted_end(user_id)
		unmoot_in = unmoot_time - time.time()
		await asyncio.sleep(unmoot_in)
		if (await db.get_mooted_end(user_id) != unmoot_time):
			return print('Moot seems to have been extended.')

	for guild in client.guilds:
		member = guild.get_member(user_id)
		if not member: continue

		mooted_role_id = get_role_id(guild.id, 'mooted')
		mooted_role = guild.get_role(mooted_role_id)

		await member.remove_roles(mooted_role, reason=reason)

	await db.set_moot_end(user_id, time.time())

	# await member.send(embed=discord.Embed(
	# 	description='You have been unmooted.'
	# ))


async def custom_reaction_messages(payload):
	# ignore reactions from mat
	# if payload.user_id == 856340031999311872:
	# 	return
	if payload.message_id == 732551899374551171:
		if str(payload.emoji.name).lower() != 'disagree':
			message = await client.get_channel(720258155900305488).fetch_message(732551899374551171)
			await message.clear_reaction(payload.emoji)

		if payload.message_id not in {732552573806051328, 732552579531407422}: return
		message = await client.get_channel(720258155900305488).fetch_message(payload.message_id)
		await message.clear_reaction(payload.emoji)
	if payload.message_id == 741806331484438549:
		if str(payload.emoji.name).lower() != 'disagree':
			message = await client.get_channel(720258155900305488).fetch_message(741806331484438549)
			await message.remove_reaction(payload.emoji, payload.member)
	elif payload.message_id == 756691321917276223:  # Blurrzy art
		if str(payload.emoji.name).lower() != 'agree':
			message = await client.get_channel(720258155900305488).fetch_message(756691321917276223)
			await message.remove_reaction(payload.emoji, payload.member)
			bot_commands_channel = config.channels['bot-commands']
			await payload.member.send(
				f'Hey, you\'re a dum dum. If you disagree, please do `!gulag 15m` in <#{bot_commands_channel}>. Thanks!'
			)


@client.event
async def on_raw_reaction_add(payload):
	await custom_reaction_messages(payload)
	await starboard.on_raw_reaction_add(payload)

def api_get_members():
	guild_id = config.main_guild
	guild = client.get_guild(guild_id)

	if not guild: return {}
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


command_modules: List[Any] = []
for module_filename in os.listdir('./forumsweats/commands'):
	if module_filename == '__init__.py' or module_filename[-3:] != '.py':
		continue
	module: Any = importlib.import_module('forumsweats.commands.' + module_filename[:-3])
	command_modules.append(module)
	print('Registering command from file', module_filename)
	commandparser.command(
		module.name,
		aliases=getattr(module, 'aliases', []),
		pad_none=getattr(module, 'pad_none', True),
		channels=getattr(module, 'channels', ['bot-commands']),
		roles=getattr(module, 'roles', [])
	)(module.run)


async def check_bobux_roles(member_id: int, bobux: Union[int, None]=None):
	if bobux is None:
		bobux = await db.get_bobux(member_id)

	guild_id = config.main_guild

	applicable_bobux_roles_names = []
	all_bobux_roles_names = ['100bobux', 'rich', 'veryrich', 'superrich']

	guild = client.get_guild(guild_id)
	member = guild.get_member(member_id)

	if not member:
		# Member isn't in the server, doesn't need roles
		return

	if bobux >= 100:
		applicable_bobux_roles_names.append('100bobux')
	if bobux >= 1000:
		applicable_bobux_roles_names.append('rich')
	if bobux >= 5000:
		applicable_bobux_roles_names.append('veryrich')
	if bobux >= 50000:
		applicable_bobux_roles_names.append('superrich')
		

	add_roles = []
	remove_roles = []
	for role_name in applicable_bobux_roles_names:
		role_id = get_role_id(guild_id, role_name)
		role = guild.get_role(role_id)
		if role not in member.roles:
			add_roles.append(role)

	for role_name in all_bobux_roles_names:
		if role_name not in applicable_bobux_roles_names:
			role_id = get_role_id(guild_id, role_name)
			role = guild.get_role(role_id)
			if role in member.roles:
				remove_roles.append(role)

	if add_roles:
		await member.add_roles(*add_roles)
	if remove_roles:
		await member.remove_roles(*remove_roles)

