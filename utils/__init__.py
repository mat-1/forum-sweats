import config

roles = config.roles


def get_role_id(guild_id, rank_name):
	return roles.get(str(guild_id), {}).get(rank_name)


def seconds_to_string(actual_seconds: int, extra_parts: int=1):
	seconds = int(actual_seconds)
	minutes = int(actual_seconds // 60)
	hours = int(actual_seconds // (60 * 60))
	days = int(actual_seconds // (60 * 60 * 24))
	remaining_seconds = actual_seconds
	if days > 0:
		remaining_seconds -= days * 60 * 60 * 24
	elif hours > 0:
		remaining_seconds -= hours * 60 * 60
	elif minutes > 0:
		remaining_seconds -= minutes * 60
	elif seconds > 0:
		remaining_seconds -= seconds

	if days >= 2:
		time_string = f'{days} days'
	elif days == 1:
		time_string = '1 day'
	elif hours >= 2:
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
	if remaining_seconds > 1 and extra_parts != 0:
		second_time_string = seconds_to_string(remaining_seconds, extra_parts=extra_parts - 1)
		time_string = f'{time_string} and {second_time_string}'
	return time_string


def trim_string(string, width=150, height=20):
	# shortens a string and adds ellipses if it's too long
	was_trimmed = False
	new_string = ''
	x_pos = 0
	y_pos = 0
	for character in string:
		if character == '\n':
			y_pos += 1
			x_pos = 0
		x_pos += 1
		if x_pos > width:
			y_pos += 1
			x_pos = 0
		if y_pos > height:
			was_trimmed = True
			break
		new_string += character

	if was_trimmed:
		new_string += '...'
	return new_string


confirmed_emoji = '👍'
