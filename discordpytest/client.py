from discord.flags import Intents
from discord.types.user import User
from discordpytest.http import FakeHTTPClient
from typing import Union
import discord
import asyncio


class FakeClient(discord.Client):
	http: FakeHTTPClient
	ws: None

	def __init__(self, client):
		self.ws = None
		self.loop = asyncio.get_event_loop()
		asyncio.set_event_loop(self.loop)
		self._listeners = client._listeners

		self.http = FakeHTTPClient(self)

		self._handlers = client._handlers

		self._hooks = client._hooks

		self._connection = self._get_state(intents=client.intents)
		self._closed = False
		self._ready = asyncio.Event()
		self._connection._get_websocket = self._get_websocket
		self._connection._get_client = lambda: self

		for attr in dir(client):
			if attr.startswith('on_'):
				setattr(self, attr, getattr(client, attr))

	async def connect(self, *, reconnect=True, id: int):
		self._connection.guild_ready_timeout = 0
		self._connection.parse_ready({
			'user': make_user_data(id),
			'guilds': []
		})

	def login(self, token, *, bot=True):
		self.loop.run_until_complete(self.http.static_login(token.strip()))

	def start(self, *args, id: int, **kwargs):
		bot = kwargs.pop('bot', True)
		reconnect = kwargs.pop('reconnect', True)

		self.login(*args, bot=bot)
		self.loop.run_until_complete(self.connect(reconnect=reconnect, id=id))

def make_user_data(user_id: Union[int, str] = 1, username: str = 'user', discriminator: str = '0001', avatar: str = '') -> User:
	return {
		'id': str(user_id),
		'username': username,
		'discriminator': str(discriminator),
		'avatar': avatar,
		'bot': False,
	}
