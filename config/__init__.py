from typing import Any, Dict
import json


def read_config_file(name):
	'Reads a json file from config/{name}.json'
	with open(f'config/{name}.json', 'r') as f:
		config_data = json.loads(f.read())
	return config_data


class AnyListMatcher:
	# Matches if the items are equal, or if the other item is inside self
	def __init__(self, data):
		self.data = data

	def __eq__(self, other):
		return self.data == other or (isinstance(self.data, list) and other in self.data)
	
	def __ne__(self, other):
		return not self.__eq__(other)

	def __str__(self):
		return str(self.data)

	def __repr__(self):
		return repr(self.data)

	def __int__(self):
		return self.data[0] if isinstance(self.data, list) else self.data

	def __hash__(self):
		return hash(self.data)
	
	def __getitem__(self, index):
		if isinstance(self.data, list):
			return self.data[index]
		elif index == 0:
			return self.data
		else:
			raise IndexError(f'{self.data} is not a list')


bot_data = read_config_file('bot')

roles: Dict[str, int] = read_config_file('roles')
channels_raw = read_config_file('channels')
channels: Dict[str, Any] = {
	channel_name: AnyListMatcher(channels_raw[channel_name]) for channel_name in channels_raw
}
prefix: str = bot_data.get('prefix', '!')
main_guild: int = bot_data.get('main_guild')

if not main_guild:
	raise ValueError('No main guild specified in bot.json.')
