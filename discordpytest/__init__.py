import discord
import asyncio
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


class FakeClient(discord.Client):
	def __init__(self, client):
		self.ws = None
		self.loop = asyncio.get_event_loop()
		self._listeners = client._listeners

		self.http = FakeHTTPClient()

		self._handlers = client._handlers

		self._hooks = client._hooks

		self._connection = self._get_state()
		self._closed = False
		self._ready = asyncio.Event()
		self._connection._get_websocket = self._get_websocket
		self._connection._get_client = lambda: self

		for attr in dir(client):
			if attr.startswith('on_'):
				setattr(self, attr, getattr(client, attr))

	def connect(self, *, reconnect=True):
		print('connect :)')

	def login(self, token, *, bot=True):
		self.http.static_login(token.strip(), bot=bot)

	def start(self, *args, **kwargs):
		bot = kwargs.pop('bot', True)
		reconnect = kwargs.pop('reconnect', True)

		self.login(*args, bot=bot)
		self.connect(reconnect=reconnect)

		print('started')


class FakeHTTPClient():
	def __init__(self):
		self.messages_queue = []

	def recreate(self):
		pass

	async def ws_connect(self, url, *, compress=0):
		print('ws connect')

	async def request(self, route, *, files=None, **kwargs):
		pass
		print('request', route, kwargs)

	def static_login(self, token, *, bot):
		print('logged in')
		self.token = token
		self.bot_token = bot

	async def get_gateway(self, *, encoding='json', v=6, zlib=True):
		return 'https://discord.com'

	async def send_message(self, channel_id, content, *, tts=False, embed=None, nonce=None, allowed_mentions=None):
		self.messages_queue.append({
			'channel_id': channel_id,
			'content': content,
			'tts': tts,
			'embed': embed,
			'nonce': nonce,
			'allowed_mentions': allowed_mentions
		})


class Tester:
	def __init__(self, client):
		self.client = FakeClient(client)

		self.client.start('-.-.-')

		print('starting')

	def make_guild(self, id=0):
		data = {
			'id': id,
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
			'roles': [],
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
		}
		self.client._connection.parse_guild_create(data)
		return self.client._connection._get_guild(int(data['id']))

	def make_channel(self, guild_id, **kwargs):
		data = {
			'id': id,
			'guild_id': guild_id,
			'type': 0,
			'name': 'general',
			'position': 0,
		}
		data.update(kwargs)

		self.client._connection.parse_channel_create(data)
		return self.client._connection.get_channel(int(data['id']))

	async def message(self, content, channel, **kwargs):
		author = {
			'id': '1',
			'username': 'mat',
			'discriminator': '6207',
			'avatar': '',
			'bot': False,
			'system': False,
			'mfa_enabled': False,
			'locale': 'en-US',
			'flags': 0,
			'premium_type': 0,
			'public_flags': 0
		}
		member = {
			'nick': None,
			'roles': [],
			'joined_at': '1970-01-01T00:00:01+00:00',
			'deaf': False,
			'mute': False
		}
		data = {
			'id': '0',
			'channel_id': channel.id,
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
			'message_reference': None,
			'author': author,
			'member': member
		}

		self.client._connection.parse_message_create(data)
		await asyncio.sleep(5)

	def verify_message(self, checker):
		if isinstance(checker, str):
			check_content = checker
			checker = lambda s: s['content'] == check_content

		# while len(bot.client.http.messages_queue) == 0:
		# 	await asyncio.sleep(0)
		assert checker(self.client.http.messages_queue[0])

