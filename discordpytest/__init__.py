from typing import Union
from discord.member import Member
from discord.user import User
from discord.role import Role
import discord
import asyncio
import random
import time


class FakeClient(discord.Client):
    def __init__(self, client):
        self.ws = None
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)
        self._listeners = client._listeners

        self.http = FakeHTTPClient(self)

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

    async def connect(self, *, reconnect=True, id: int):
        self._connection.guild_ready_timeout = 0
        self._connection.parse_ready({
            'user': Tester.make_user_data(id),
            'guilds': []
        })

    def login(self, token, *, bot=True):
        self.loop.run_until_complete(self.http.static_login(token.strip()))

    def start(self, *args, id: int, **kwargs):
        bot = kwargs.pop('bot', True)
        reconnect = kwargs.pop('reconnect', True)

        self.login(*args, bot=bot)
        self.loop.run_until_complete(self.connect(reconnect=reconnect, id=id))


class FakeHTTPClient():
    def __init__(self, client):
        self.messages_queue = []
        self.client = client

    def recreate(self):
        pass

    async def ws_connect(self, url, *, compress=0):
        pass

    async def static_login(self, token):
        self.token = token

    async def get_gateway(self, *, encoding='json', v=6, zlib=True):
        return 'https://discord.com'

    async def send_message(
        self,
        channel_id,
        content,
        *,
        tts=False,
        embed=None,
        embeds=None,
        nonce=None,
        allowed_mentions=None,
        message_reference=None,
        stickers=None,
        components=None,
    ):
        self.messages_queue.append({
            'channel_id': channel_id,
            'content': content,
            'tts': tts,
            'embeds': [embed] if embed else embeds,
            'nonce': nonce,
            'allowed_mentions': allowed_mentions,
            'message_reference': message_reference,
            'components': components,
            'sticker_ids': stickers
        })
        user_json = self.client._connection.user._to_minimal_user_json()
        return {
            'id': random.randint(100000, 99999999999999),
            'channel_id': channel_id,
            'guild_id': self.client.get_channel(channel_id).guild.id,
            'author': user_json,
            'member': {
                'user': user_json,
                'nick': None,
                'roles': [],
                'joined_at': '1970-01-01T00:00:01+00:00'
            },
            'content': content,
            'timestamp': '1970-01-01T00:00:01+00:00',
            'edited_timestamp': None,
            'tts': tts,
            'mention_everyone': False,
            'mentions': [],
            'mention_roles': [],
            'mention_channels': [],
            'attachments': [],
            'embeds': [],
            'pinned': False,
            'type': 0,
        }

    async def send_typing(self, channel_id):
        pass

    async def add_reaction(self, channel_id, message_id, emoji):
        print('add reaction!')

    async def add_role(self, guild_id, user_id, role_id, *, reason=None):
        print('add role!')


class Tester:
    def __init__(self, client):
        self.client = FakeClient(client)

        self.client.start('-.-.-', id=719348452491919401)

        self.client._connection.user = self.make_user(719348452491919401)

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
        default_role = Role(guild=guild, state=self.client._connection, data={
            'id': str(guild.id),
            'name': '@everyone',
            'color': '000000',
            'hoist': True,
            'position': 0,
            'permissions': 0,
            'managed': False,
            'mentionable': False
        })
        guild._roles[default_role.id] = default_role
        # the bot is always a member of the guild
        self.make_member(guild, self.client._connection.user)
        return guild

    def make_channel(self, guild, **kwargs):
        data = {
            'id': id,
            'guild_id': guild.id,
            'type': 0,
            'name': 'general',
            'position': 0,
        }
        data.update(kwargs)

        self.client._connection.parse_channel_create(data)
        return self.client._connection.get_channel(int(data['id']))

    @staticmethod
    def make_user_data(user_id: Union[int, str] = 1, username: str = 'user', discriminator: str = '0001', avatar: str = '') -> User:
        return {
            'id': str(user_id),
            'username': username,
            'discriminator': str(discriminator),
            'avatar': avatar,
            'bot': False,
        }

    def make_user(self, user_id=1, username='user', discriminator='0001', avatar=''):
        data = Tester.make_user_data(user_id, username, discriminator, avatar)
        return self.client._connection.store_user({
            'avatar': data['avatar'],
            'bot': data['bot'],
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

    def make_member(self, guild, user):
        data = {
            'user': user._to_minimal_user_json(),
            'nick': None,
            'roles': [],
            'joined_at': '1970-01-01T00:00:01+00:00'
        }
        member = Member(data=data, state=self.client._connection, guild=guild)
        guild._add_member(member)
        guild._member_count = len(guild._members)
        return member

    async def message(self, content, channel, author=None, **kwargs):
        if not author:
            author = self.make_member(channel.guild, self.make_user())
        author_data = {
            'user': author._user._to_minimal_user_json(),
            'nick': author.nick,
            'roles': author._roles,
            'joined_at': author.joined_at.isoformat(),
        }
        member = Member(state=self.client._connection,
                        data=author_data, guild=channel.guild)
        data = {
            'id': '0',
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
            'member': author_data
        }
        data.update(kwargs)
        self.client._connection.parse_message_create(data)

    async def verify_message(self, checker, timeout=1):
        if isinstance(checker, str):
            check_content = checker

            def checker(s):
                return s['content'] == check_content

        started_time = time.time()

        while len(self.client.http.messages_queue) == 0:
            await asyncio.sleep(0)
            elapsed_time = time.time() - started_time
            if elapsed_time > timeout:
                raise TimeoutError()

        message = self.client.http.messages_queue.pop(0)
        assert checker(message)
