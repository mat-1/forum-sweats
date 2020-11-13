import json


def read_config_file(name):
	'Reads a json file from config/{name}.json'
	with open(f'config/{name}.json', 'r') as f:
		config_data = json.loads(f.read())
	return config_data


bot_data = read_config_file('bot')

roles = read_config_file('roles')
prefix = bot_data.get('prefix', '!')
main_guild = bot_data.get('main_guild')

if not main_guild:
	raise ValueError('No main guild specified in bot.json.')
