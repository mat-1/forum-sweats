from __future__ import annotations

from discord.types.snowflake import Snowflake
from typing import Any, Dict, List
from discord.types import channel
import random

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from discordpytest.client import FakeClient


class FakeHTTPClient():
	def __init__(self, client: FakeClient):
		self.queues: Dict[str, List[Any]] = {}
		self.client = client
	
	def add_to_queue(self, queue_name: str, value: Any):
		if queue_name not in self.queues:
			self.queues[queue_name] = []
		self.queues[queue_name].append(value)
	
	def get_queue(self, queue_name: str) -> List[Any]:
		return self.queues.get(queue_name, [])
	
	def pop_queue(self, queue_name: str) -> Any:
		if queue_name in self.queues:
			return self.queues[queue_name].pop(0)
		return None
	
	def set_queue(self, queue_name: str, value: List[Any]):
		self.queues[queue_name] = value

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
		embeds_data = [embed] if embed else embeds or []
		self.add_to_queue('send_message', {
			'channel_id': channel_id,
			'content': content,
			'tts': tts,
			'embeds': embeds_data,
			'nonce': nonce,
			'allowed_mentions': allowed_mentions,
			'message_reference': message_reference,
			'components': components,
			'sticker_ids': stickers
		})
		user_json = self.client._connection.user._to_minimal_user_json()
		channel = self.client.get_channel(channel_id)
		return {
			'id': random.randint(100000, 99999999999999),
			'channel_id': channel_id,
			'guild_id': channel.guild.id if (channel is not None and hasattr(channel, 'guild')) else None,
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
			'embeds': embeds_data,
			'pinned': False,
			'type': 0,
		}
	
	async def delete_message(self, channel_id, message_id, *, reason = None):
		self.add_to_queue('delete_message', {
			'channel_id': str(channel_id),
			'message_id': str(message_id),
			'reason': reason
		})
	
	async def start_private_message(self, user: Snowflake) -> channel.DMChannel:
		self.add_to_queue('start_private_message', {
			'user_id': str(user)
		})

		user_object = self.client.get_user(int(user))
		if not user_object:
			# the user doesn't exist, throw an error
			raise Exception('User does not exist')

		user_json = user_object._to_minimal_user_json()
		return {
			'id': random.randint(100000, 99999999999999),
			'name': 'dm',
			'recipients': [
				user_json
			],
			'type': 1,
		}
	
	async def logs_from(
        self,
        channel_id,
        limit,
        before = None,
        after = None,
        around = None,
    ):
		# uhhhh yeah no thanks i'll pass
		return []



	async def send_typing(self, channel_id):
		pass

	async def add_reaction(self, channel_id, message_id, emoji):
		reaction = {
			'channel_id': str(channel_id),
			'message_id': str(message_id),
			'emoji': emoji
		}
		self.add_to_queue('add_reaction', reaction)
		print('added reaction!')

	async def add_role(self, guild_id, user_id, role_id, *, reason=None):
		print('add role!')