import json

with open('roles.json', 'r') as f:
	roles = json.loads(f.read())


def get_role_id(guild_id, rank_name):
	return roles.get(str(guild_id), {}).get(rank_name)
