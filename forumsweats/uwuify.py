import random
import re


extras = (
	'uwu',
	'owo',
	':3',
	'o3o',
	'hehe',
	';)'
)


def add_nyvowel(message):
	message = re.sub(r'n([aeiou])', r'ny\1', message)
	message = re.sub(r'N([aeiou])', r'Ny\1', message)
	message = re.sub(r'N([AEIOU])', r'NY\1', message)
	message = re.sub(r'n([AEIOU])', r'nY\1', message)
	return message


def add_extras(message):
	output = ''
	previous_character = ''
	extra_chance = .7
	sentence_length = 0
	sentence_uppercase_count = 0
	sentence_lowercase_count = 0
	sentence_enders = '.!?'

	for character in message:
		if previous_character in sentence_enders and character == ' ':
			if random.random() <= extra_chance and sentence_length > 10:
				face = random.choice(extras)

				if sentence_uppercase_count / sentence_length >= .9:
					# if 90% of the sentence is uppercase, make the face uppercase as well
					face = face.upper()

				output = output[:-1] + ' ' + face + output[-1]
			sentence_length = 0
			sentence_uppercase_count = 0
			sentence_lowercase_count = 0
		else:
			sentence_length += 1
			if character.isupper():
				sentence_uppercase_count += 1
			if character.islower():
				sentence_lowercase_count += 1
		output += character
		previous_character = character

	if random.random() <= extra_chance and sentence_length > 10:
		face = random.choice(extras)

		if sentence_uppercase_count / sentence_length >= .9:
			# if 90% of the sentence is uppercase, make the face uppercase as well
			face = face.upper()

		if previous_character in sentence_enders:
			output = output[:-1] + ' ' + face + output[-1]
		else:
			output += ' ' + face

	return output


def uwuify(message, limit=2000):
	uwuized_message = message\
		.replace('@', '')\
		.replace('r', 'w')\
		.replace('l', 'w')\
		.replace('R', 'W')\
		.replace('L', 'W')\
		.replace('<!642466378254647296>', '<@642466378254647296>')

	temp_uwuized_message = add_nyvowel(uwuized_message)
	if len(temp_uwuized_message) < limit: uwuized_message = temp_uwuized_message

	temp_uwuized_message = add_extras(uwuized_message)
	if len(temp_uwuized_message) < limit: uwuized_message = temp_uwuized_message

	return uwuized_message
