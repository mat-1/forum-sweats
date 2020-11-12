import json


def read_config_file(name):
	'Reads a json file from config/{name}.json'
	with open(f'config/{name}.json', 'r') as f:
		config_data = json.loads(f.read())
	return config_data


roles = read_config_file('roles')
