import json

with open('roles.json', 'r') as f:
	roles = json.loads(f.read())


def get_role_id(guild_id, rank_name):
	return roles.get(str(guild_id), {}).get(rank_name)


def seconds_to_string(actual_seconds, extra_parts=1):
	seconds = int(actual_seconds)
	minutes = int(actual_seconds // 60)
	hours = int(actual_seconds // (60 * 60))
	remaining_seconds = actual_seconds
	if hours > 0:
		remaining_seconds -= hours * 60 * 60
	elif minutes > 0:
		remaining_seconds -= minutes * 60
	elif seconds > 0:
		remaining_seconds -= seconds

	if hours >= 2:
		time_string = f'{hours} hours'
	elif hours == 1:
		time_string = '1 hour'
	elif minutes >= 2:
		time_string = f'{minutes} minutes'
	elif minutes == 1:
		time_string = '1 minute'
	elif seconds == 1:
		time_string = '1 second'
	else:
		time_string = f'{seconds} seconds'
	print('remaining_seconds', remaining_seconds)
	if remaining_seconds > 1 and extra_parts != 0:
		second_time_string = seconds_to_string(remaining_seconds, extra_parts=extra_parts - 1)
		time_string = f'{time_string} and {second_time_string}'
	return time_string
