from . import discordbot
from typing import Any, Coroutine, List, Optional, Union
import traceback
import discord
import config
import time
import re


class Member(discord.Member):
	avatar: discord.Asset
	id: int
	mention: str

	async def send(self, message: str): pass

	async def convert(self, ctx, arg):
		arg = arg.strip()
		if len(arg) == 0:
			return None
		if arg[0] == '@':
			arg = arg[1:]

		CHECKERS = [
			check_user_id,  # Check user id
			check_mention,  # Check mention
			check_name_with_discrim,  # Name + discrim

			check_name_starts_with_recent,  # Name starts with
			check_name_starts_with,  # Name starts with

			check_nickname_recent,  # Nickname
			check_nickname,  # Nickname

			check_nickname_starts_with_recent,  # Nickname starts with
			check_nickname_starts_with,  # Nickname starts with

			check_name_contains_recent,  # Name contains
			check_name_contains,  # Name contains

			check_nickname_contains_recent,  # Nickname contains
			check_nickname_contains,  # Nickname contains

			check_fakemember_id  # Deleted member id
		]
		for checker in CHECKERS:
			member = checker(ctx, arg)
			if member is not None:
				return member

		return None


class Context(discord.Message):  # very unfinished but its fine probably
	__slots__ = ('message', 'channel', 'guild', 'author', 'prefix', 'client', 'content', 'add_reaction', 'delete', 'edit', 'command_name')

	message: discord.Message
	content: str
	channel: discord.abc.Messageable
	guild: discord.Guild
	author: Member
	prefix: Optional[str]
	client: discord.Client
	command_name: Optional[str]

	async def send(self, *args, embed=None, **kwargs):
		'Send a message to a channel'
		message = await self.message.channel.send(*args, **kwargs, embed=embed)
		return message

	async def reply(self, content: Union[str, None] = None, **kwargs):
		message = await self.message.reply(content, **kwargs)
		return message

	def __init__(self, message, prefix=None, command_name=None):
		'Initialize all the things'
		self.message = message
		self.content = message.content
		self.channel = message.channel
		self.guild = message.guild
		self.author = message.author

		self.add_reaction = message.add_reaction
		self.delete = message.delete

		self.prefix = prefix
		self.command_name = command_name
		self.client = discordbot.client


class NothingFound(BaseException): pass


recent_members = {}


class CommandParser():
	functions = []

	def __init__(self, prefix, bot_id):
		'''
		All the bot prefixes.
		Also allows pings
		'''
		self.prefixes = [
			prefix,
			f'<@{bot_id}>',
			f'<@!{bot_id}>'
		]

	async def try_converter(self, ctx, string: str, converter):
		if hasattr(converter, 'convert'):
			return await converter.convert(converter, ctx, string)
		try:
			return converter(string)
		except ValueError:
			return

	async def parse_args(self, parsing_remaining, func, ctx, ignore_extra=True):
		'''
		Parses the command arguments
		'''
		# Annotations are the expected types (str, int, Member, etc)
		expected_types = func.__annotations__
		# Args is all the arguments for the function
		args = func.__code__.co_varnames[1:]  # [1:] to skip ctx
		return_args = []
		for argnum, arg in enumerate(args):
			if arg in expected_types:
				converter = expected_types[arg]
				found = None
				i = 0
				for i in reversed([pos for pos, char in enumerate(parsing_remaining + ' ') if char == ' ']):
					cmd_arg = parsing_remaining[:i]
					tried = await self.try_converter(ctx, cmd_arg, converter)
					if tried is not None:
						found = tried
						break
				if found:
					parsing_remaining = parsing_remaining[i + 1:]
					if isinstance(found, str):
						found = found.strip()
					return_args.append(found)
				else:
					parsing_remaining = (parsing_remaining + ' ').split(' ', len(args) - argnum)[-1]
					return_args.append(None)
			else:
				cmd_arg, parsing_remaining = (parsing_remaining + ' ').split(' ', 1)
				if cmd_arg:
					if isinstance(cmd_arg, str):
						cmd_arg = cmd_arg.strip()
					return_args.append(cmd_arg)
		if parsing_remaining.strip():
			if not ignore_extra:
				raise Exception('Extra data left')
		return return_args

	async def process_commands(self, message):
		global recent_members
		recent_members[message.author] = time.time()
		if message.author.bot:
			return
		parsing_remaining = message.content.replace('  ', ' ')
		found = False

		# set the prefix as an empty string as a placeholder
		prefix: str = ''
		for prefix in self.prefixes:
			if parsing_remaining.startswith(prefix):
				found = True
				break
				
		# if no suitable prefix was found, just return
		if not found: return
		parsing_remaining = parsing_remaining[len(prefix):].strip()

		# figure out the command name
		matching_command = None
		for function in self.functions:
			command_name = function[0]
			if parsing_remaining.lower().startswith(command_name + ' ') or parsing_remaining.lower() == command_name:
				# only replace the known matching command if there's none of if this one is longer
				if not matching_command or len(command_name) > len(matching_command):
					matching_command = command_name

		# if no matching command was found, return
		if not matching_command: return
		command_name = matching_command

		parsing_remaining = parsing_remaining[len(command_name):].strip()
		for function in self.functions:
			if function[0] != command_name: continue
			func, channels, pad_none, roles = function[1]

			# if roles exists and the user doesnt have any of the roles, return
			if roles and not any(discordbot.has_role(message.author.id, role) for role in roles):
				return

			# if it's in a dm and dm isn't one of the allowed channels, return
			if not message.guild and 'dm' not in channels:
				return

			if channels is not None and not any(config.channels[channel] == message.channel.id for channel in channels):
				return

			ctx = Context(message, prefix=prefix, command_name=command_name)
			if parsing_remaining:
				try:
					return_args = await self.parse_args(parsing_remaining, func, ctx, ignore_extra=pad_none)
				except Exception as e:
					traceback.print_exc()
					print('error parsing?', type(e), e, func.__code__.co_filename)
					continue
			else:
				return_args = []
			
			# try adding None as an argument
			for attempt in range(10):
				try:
					print('doing function', func.__code__.co_filename)
					return await func(ctx, *return_args)
				except TypeError as e:
					traceback.print_exc()
					if pad_none:
						return_args.append(None)
					else:
						break
				except BaseException as e:
					print('error :(')
					traceback.print_exc()
					return

	def command(self, name: str, aliases: List[str]=[], channels: List[str]=['bot-commands'], pad_none: bool=True, roles: List[str]=[]):
		def decorator(func):
			command_names = [name] + list(aliases)
			for command_name in command_names:
				self.functions.append((command_name.lower(), (func, channels, pad_none, roles)))
			return func
		return decorator


def get_recent_members():
	'Gets members that talked in chat in the past hour'
	members = []
	for member in dict(recent_members):
		if recent_members[member] < 60 * 60:
			members.append(member)
		else:
			del recent_members[member]
	return members


'''
Member
'''


def get_channel_members(channel_id):
	try:
		return discordbot.client.get_channel(channel_id).members
	except:
		return [ discordbot.client.get_channel(channel_id).recipient ]


def get_guild_members(channel_id):
	try:
		members = discordbot.client.get_guild(channel_id).members
	except Exception as e:
		members = [ discordbot.client.get_channel(channel_id).recipient ]
	return sorted(members, key=lambda m: len(m.name))


def check_user_id(ctx, arg):
	try:
		if ctx.guild:
			member = ctx.guild.get_member(int(arg))
		else:
			member = ctx.client.get_user(int(arg))
		if member is not None:
			return member
	except ValueError:
		pass


def check_mention(ctx, arg):
	match = re.match(r'^<@!?(\d+)>$', arg)

	if match:
		user_id = match.group(1)
		try:
			member = ctx.guild.get_member(int(user_id))
			if member is not None:
				return member
			for guild in discordbot.client.guilds:
				member = guild.get_member(int(user_id))
				if member is not None:
					return member
		except ValueError:
			# doesnt happen i think
			# but i dont want to break it
			pass


def check_name_with_discrim(ctx, arg):
	member = discord.utils.find(
		lambda m: str(m).lower() == arg.lower(),
		get_guild_members(ctx.guild.id)
	)
	return member


def check_name_without_discrim(ctx, arg):
	member = discord.utils.find(
		lambda m: m.name.lower() == arg.lower(),
		get_guild_members(ctx.guild.id)
	)
	return member


def check_nickname(ctx, arg):
	member = discord.utils.find(
		lambda m: m.display_name.lower() == arg.lower(),
		get_guild_members(ctx.guild.id)
	)
	return member


def check_nickname_recent(ctx, arg):
	member = discord.utils.find(
		lambda m: m.display_name.lower() == arg.lower(),
		get_recent_members()
	)
	return member


def check_name_starts_with(ctx, arg):
	members = list(filter(
		lambda m: m.name.lower().startswith(arg.lower()),
		get_guild_members(ctx.guild.id)
	))
	if members:
		return members[0]


def check_name_starts_with_recent(ctx, arg):
	member = discord.utils.find(
		lambda m: m.name.lower().startswith(arg.lower()),
		get_recent_members()
	)
	return member


def check_nickname_starts_with(ctx, arg):
	members = list(filter(
		lambda m: m.display_name.lower().startswith(arg.lower()),
		get_guild_members(ctx.guild.id)
	))
	if members:
		return list(sorted(members, key=lambda m: len(m.display_name)))[-1]


def check_nickname_starts_with_recent(ctx, arg):
	member = discord.utils.find(
		lambda m: m.display_name.lower().startswith(arg.lower()),
		get_recent_members()
	)
	return member


def check_name_contains(ctx, arg):
	member = discord.utils.find(
		lambda m: arg.lower() in m.name.lower(),
		get_guild_members(ctx.guild.id)
	)
	return member


def check_name_contains_recent(ctx, arg):
	member = discord.utils.find(
		lambda m: arg.lower() in m.name.lower(),
		get_recent_members()
	)
	return member


def check_nickname_contains(ctx, arg):
	member = discord.utils.find(
		lambda m: arg.lower() in m.display_name.lower(),
		get_guild_members(ctx.guild.id)
	)
	return member


def check_nickname_contains_recent(ctx, arg):
	member = discord.utils.find(
		lambda m: arg.lower() in m.display_name.lower(),
		get_recent_members()
	)
	return member

def check_fakemember_id(ctx, arg):
	try:
		return FakeMember(int(arg))
	except ValueError:
		pass

class FakeMember():
	def __init__(self, id):
		self.id = id
		self.name = '<Dummy>'
		self.display_name = self.name
		self.discriminator = '0000'
		self.mention = f'<@{self.id}>'

	def __str__(self):
		return f'{self.name}#{self.discriminator}'

	async def add_roles(self, *args, **kwargs):
		pass

	async def remove_roles(self, *args, **kwargs):
		pass



'''
Time converter
'''

lengths = {
	'milliseconds': 1 / 1000,
	'millisecond': 1 / 1000,
	'ms': 1 / 1000,

	'seconds': 1,
	'second': 1,
	's': 1,

	'minutes': 1 * 60,
	'minute': 1 * 60,
	'mins': 1 * 60,
	'min': 1 * 60,
	'm': 1 * 60,

	'hours': 1 * 60 * 60,
	'hour': 1 * 60 * 60,
	'hrs': 1 * 60 * 60,
	'hr': 1 * 60 * 60,
	'h': 1 * 60 * 60,

	'days': 1 * 60 * 60 * 24,
	'day': 1 * 60 * 60 * 24,
	'd': 1 * 60 * 60 * 24,

	'weeks': 1 * 60 * 60 * 24 * 7,
	'week': 1 * 60 * 60 * 24 * 7,
	'w': 1 * 60 * 60 * 24 * 7,

	'months': 1 * 60 * 60 * 24 * 30,
	'month': 1 * 60 * 60 * 24 * 30,
	'mo': 1 * 60 * 60 * 24 * 30,

	'years': 1 * 60 * 60 * 24 * 365,
	'year': 1 * 60 * 60 * 24 * 365,
	'y': 1 * 60 * 60 * 24 * 365,

	'eons': 1 * 60 * 60 * 24 * 365 * 1000000000,
	'eon': 1 * 60 * 60 * 24 * 365 * 1000000000,
	'e': 1 * 60 * 60 * 24 * 365 * 1000000000,
	'aeon': 1 * 60 * 60 * 24 * 365 * 1000000000,
	'aeons': 1 * 60 * 60 * 24 * 365 * 1000000000,

	'antisynth': 1 * 60 * 60 * 24 * 365 * 1000000000 * 99999999999999999999,
	'antisynths': 1 * 60 * 60 * 24 * 365 * 1000000000 * 99999999999999999999,

	'yoctosecond': 1 / 1000000000000000000000000,
	'yoctoseconds': 1 / 1000000000000000000000000,
}


def check_time(ctx, arg: str):
	total_time = 0
	while arg:
		if arg.strip() == 'forever':
			return lengths['eons'] * 1000
		time_part = ''
		for char in arg:
			if char in '0123456789':
				time_part += char
			else:
				break
		split_time_type_and_arg = arg[len(time_part):].strip().split(' ', 1)
		if len(split_time_type_and_arg) > 1:
			time_type, arg = split_time_type_and_arg
		else:
			time_type = split_time_type_and_arg[0]
			arg = ''

		try:
			time_part = int(time_part)
		except:
			return
		if time_type in lengths:
			total_time += lengths[time_type] * time_part
		else:
			return
	return total_time


class Time(int):
	def __init__(self, value=0):
		self.value = value
	def __gt__(self, other) -> bool: return float(self) > float(other)
	def __lt__(self, other) -> bool: return float(self) < float(other)
	def __int__(self) -> int: return int(self.value)
	def __float__(self) -> float: return float(self.value)

	async def convert(self, ctx: Context, arg: str):
		arg = arg.strip()
		CHECKERS = [
			check_time
		]
		for checker in CHECKERS:
			length = checker(ctx, arg)
			if length is not None:
				return length

		return None
