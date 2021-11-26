from discordpytest.client import FakeClient, make_user_data
from discord.types.snowflake import Snowflake, SnowflakeList
from discord.types.user import User as UserPayload
from discord.types.member import MemberWithUser
from discord.types.channel import TextChannel
from discord.types.message import Message as MessagePayload
from typing import Callable, Dict, Union
from discord.member import Member
from discord.role import Role
from discord.user import User
import asyncio
import random
import time



class Tester:
	def __init__(self, client):
		self.client = FakeClient(client)

		self.client.start('-.-.-', id=719348452491919401)

		self.client._connection.user = self.make_user(719348452491919401)

	def clear_queues(self):
		self.client.http.queues = {}

	def make_guild(self, **kwargs):
		data = {
			'id': 0,
			'name': 'Forum Sweats',
			'icon': None,
			'splash': None,
			'discovery_splash': None,
			'owner_id': '0',
			'region': 'en-US',
			'afk_channel_id': '0',
			'afk_timeout': 0,
			'verification_level': 0,
			'default_message_notifications': 0,
			'explicit_content_filter': 0,
			'roles': {},
			'emojis': [],
			'features': [],
			'mfa_level': 0,
			'application_id': None,
			'system_channel_id': None,
			'system_channel_flags': 0,
			'rules_channel_id': None,
			'joined_at': '1970-01-01T00:00:01+00:00',
			'vanity_url_code': None,
			'description': None,
			'banner': None,
			'premium_tier': 0,
			'premium_subscription_count': 0,
			'preferred_locale': 'en-US',
			'public_updates_channel_id': None,
			'member_count': 0
		}
		data.update(kwargs)
		self.client._connection.parse_guild_create(data)
		guild = self.client.get_guild(int(data['id']))

		# sanity check, and so the typings work
		assert guild

		default_role = Role(guild=guild, state=self.client._connection, data={
			'id': str(guild.id),
			'name': '@everyone',
			'color': 0,
			'hoist': True,
			'position': 0,
			'permissions': '0',
			'managed': False,
			'mentionable': False
		})
		guild._roles[default_role.id] = default_role
		# the bot is always a member of the guild
		self.make_member(guild, self.client._connection.user)
		return guild

	def make_channel(self, guild, id: Union[str, int]):
		data: TextChannel = {
			'id': str(id),
			'guild_id': guild.id,
			'type': 0,
			'name': 'general',
			'position': 0,
			'permission_overwrites': [],
			'parent_id': None,
			'nsfw': False,
		}

		self.client._connection.parse_channel_create(data)
		return self.client._connection.get_channel(int(data['id']))

	def make_user(self, user_id: Snowflake=1, username: str='user', discriminator: str='0001', avatar: str='') -> User:
		data = make_user_data(user_id, username, discriminator, avatar)
		user = self.client._connection.store_user({
			'avatar': data['avatar'],
			'bot': data.get('bot', False),
			'discriminator': data['discriminator'],
			'email': None,
			'flags': 0,
			'id': data['id'],
			'local': '',
			'mfa_enabled': False,
			'premium_type': 0,
			'public_flags': 0,
			'system': False,
			'username': data['username'],
			'verified': False,
		})
		return user

	def make_member(self, guild, user) -> Member:
		data: MemberWithUser = {
			'user': user._to_minimal_user_json(),
			'nick': '',
			'roles': [],
			'joined_at': '1970-01-01T00:00:01+00:00',
			# not sure how deaf and mute are supposed to be  but it's fine
			'deaf': '0',
			'mute': '0',
		}
		member = Member(data=data, state=self.client._connection, guild=guild)
		guild._add_member(member)
		guild._member_count = len(guild._members)
		return member

	async def message(self, content, channel, author: Member=None, **kwargs) -> MessagePayload:
		if not author:
			author = self.make_member(channel.guild, self.make_user(0))

		user: UserPayload = author._user._to_minimal_user_json()
		roles: SnowflakeList = author._roles.tolist()

		author_data: MemberWithUser = {
			'user': user,
			'nick': author.nick or '',
			'roles': roles,
			'joined_at': author.joined_at.isoformat() if author.joined_at else '',
			'deaf': '0',
			'mute': '0',
		}

		member = Member(state=self.client._connection,
						data=author_data, guild=channel.guild)

		data = {
			'id': random.randint(100000, 99999999999999),
			'channel_id': channel.id,
			'guild_id': channel.guild.id,
			'reactions': [],
			'attachments': [],
			'embeds': [],
			'mention_roles': [],
			'application': None,
			'activity': None,
			'edited_timestamp': '1970-01-01T00:00:01+00:00',
			'type': 0,
			'pinned': False,
			'flags': 0,
			'mention_everyone': False,
			'tts': False,
			'content': content,
			'nonce': None,
			'author': author._user._to_minimal_user_json(),
			'member': author_data,
		}
		data.update(kwargs)
		self.client._connection.parse_message_create(data)

		return data
	
	async def verify_queue(self, queue_name: str, checker: Callable[[Dict], bool], timeout=1):
		started_time = time.time()

		# wait until something shows up in the queue that passes the check, or timeout
		while not any(checker(m) for m in self.client.http.get_queue(queue_name)):
			await asyncio.sleep(0)
			elapsed_time = time.time() - started_time
			if elapsed_time > timeout:
				raise TimeoutError()

		# remove the message from the queue
		self.client.http.set_queue(
			queue_name,
			[m for m in self.client.http.get_queue(queue_name) if not checker(m)]
		)

	async def verify_message(self, checker: Union[str, Callable[[MessagePayload], bool]], timeout=1):
		if isinstance(checker, str):
			check_content = checker

			checker = lambda m: m['content'] == check_content

		await self.verify_queue('send_message', checker, timeout)
	
	async def verify_message_deleted(self, message_id: int, timeout=1):
		await self.verify_queue('delete_message', lambda m: int(m['message_id']) == message_id, timeout)
	
	async def verify_reaction_added(self, checker: Union[str, Callable[[Dict], bool]], timeout=1):
		if isinstance(checker, str) or isinstance(checker, int):
			check_message_id = int(checker)

			checker = lambda m: m['message_id'] == check_message_id
		
		await self.verify_queue('add_reaction', checker, timeout)
