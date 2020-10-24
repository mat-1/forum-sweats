import discord
from discord.ext import commands
import re
import time
from . import discordbot
import traceback

# this is just so i can customize command parsing more


class Context():  # very unfinished but its fine probably
	__slots__ = ('message', 'channel', 'guild', 'author', 'prefix', 'client', 'content', 'add_reaction', 'delete', 'edit')

	async def send(self, *args, embed=None, **kwargs):
		'Send a message to a channel'
		message = await self.message.channel.send(*args, **kwargs, embed=embed)
		return message

	def __init__(self, message, prefix=None):
		'Initialize all the things'
		self.message = message
		self.content = message.content
		self.channel = message.channel
		self.guild = message.guild
		self.author = message.author

		self.add_reaction = message.add_reaction
		self.delete = message.delete

		self.prefix = prefix
		self.client = discordbot.client


class NothingFound(BaseException): pass


bot_channels = {
	717904501692170260: (
		718076311150788649,
		719518839171186698
	),  # forum sweats, bot-commands
	719349183974473851: 719349184750420010,  # bot testing, general
}

recent_members = {}


class BetterBot():
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

	async def try_converter(self, ctx, string, converter):
		if hasattr(converter, 'convert'):
			return await converter.convert(converter, ctx, string)
		try:
			return converter(string)
		except ValueError:
			return

	async def parse_args(self, parsing_left, func, ctx, ignore_extra=True):
		'''
		Parses the command arguments
		'''
		# Annotations are the expected types (str, int, Member, etc)
		ann = func.__annotations__
		# Args is all the arguments for the function
		args = func.__code__.co_varnames[1:]  # [1:] to skip ctx
		return_args = []
		for argnum, arg in enumerate(args):
			if arg in ann:
				hint = ann[arg]
				found = None
				for i in reversed([pos for pos, char in enumerate(parsing_left + ' ') if char == ' ']):
					cmd_arg = parsing_left[:i]
					tried = await self.try_converter(ctx, cmd_arg, hint)
					if tried is not None:
						found = tried
						break
				if found:
					parsing_left = parsing_left[i + 1:]
					if isinstance(found, str):
						found = found.strip()
					return_args.append(found)
				else:
					parsing_left = (parsing_left + ' ').split(' ', len(args) - argnum)[-1]
					return_args.append(None)
			else:
				cmd_arg, parsing_left = (parsing_left + ' ').split(' ', 1)
				if cmd_arg:
					if isinstance(cmd_arg, str):
						cmd_arg = cmd_arg.strip()
					return_args.append(cmd_arg)
		if parsing_left.strip():
			if not ignore_extra:
				raise Exception('Extra data left')
		return return_args

	async def process_commands(self, message):
		global recent_members
		recent_members[message.author] = time.time()
		if message.author.bot:
			return
		parsing_left = message.content.replace('  ', ' ')
		found = False
		for prefix in self.prefixes:
			if parsing_left.startswith(prefix):
				found = True
				break
		if not found: return
		parsing_left = parsing_left[len(prefix):].strip()
		command, parsing_left = (parsing_left + ' ').split(' ', 1)
		command = command.lower()
		for function in self.functions:
			if command != function[0]: continue
			func, bot_channel, pad_none = function[1]
			if bot_channel:
				if message.guild and not (
					bot_channels[message.guild.id] == message.channel.id
					or message.channel.id in bot_channels[message.guild.id]
				):
					return
			ctx = Context(message, prefix=prefix)
			if parsing_left:
				try:
					return_args = await self.parse_args(parsing_left, func, ctx, ignore_extra=pad_none)
				except Exception as e:
					print('error parsing?', type(e), e, func.__code__.co_filename)
					continue
			else:
				return_args = []
			for attempt in range(10):
				try:
					print('doing function', func.__code__.co_filename)
					return await func(ctx, *return_args)
				except TypeError:
					if pad_none:
						return_args.append(None)
					else:
						break
				except BaseException as e:
					print('error :(')
					traceback.print_exc()

	def command(self, name, aliases=[], bot_channel=True, pad_none=True):
		def decorator(func):
			for command_name in [name] + aliases:
				self.functions.append((command_name.lower(), (func, bot_channel, pad_none)))
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
		return [discordbot.client.get_channel(channel_id).recipient]


def get_guild_members(channel_id):
	try:
		members = discordbot.client.get_guild(channel_id).members
	except Exception as e:
		members = [discordbot.client.get_channel(channel_id).recipient]
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


class Member(commands.Converter):
	async def convert(self, ctx, arg):
		arg = arg.strip()
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
		]
		for checker in CHECKERS:
			member = checker(ctx, arg)
			if member is not None:
				return member

		return None


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


def check_time(ctx, arg):
	if arg.strip() == 'forever':
		return lengths['eons'] * 1000
	time_part = ''
	for char in arg:
		if char in '0123456789':
			time_part += char
		else:
			break
	time_type = arg[len(time_part):]
	time_type = time_type.strip()
	time_part = int(time_part)
	if time_type in lengths:
		return lengths[time_type] * time_part


class Time(commands.Converter):
	async def convert(self, ctx, arg):
		arg = arg.strip()
		CHECKERS = [
			check_time
		]
		for checker in CHECKERS:
			length = checker(ctx, arg)
			if length is not None:
				return length

		return None
