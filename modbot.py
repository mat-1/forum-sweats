from datetime import datetime, timedelta
from bot import discordbot
import unidecode
import aiohttp
import time
import json
import os
import re
import db

with open('letter_pairs.json', 'r') as f:
	letter_pair_scores = json.loads(f.read())
previous_user_messages = {}
last_toxic_message_times = {}
last_very_toxic_message_times = {}

perspective_key = os.getenv('perspective_key')
if not perspective_key:
	print('No perspective key found!')
perspective_url = f'https://commentanalyzer.googleapis.com/'\
	'v1alpha1/comments:analyze?key={perspective_key}'

s = aiohttp.ClientSession()


async def get_perspective_score(message, models=['SEVERE_TOXICITY', 'TOXICITY', 'IDENTITY_ATTACK']):

	input_data = {
		'comment': {
			'text': message
			.replace('shitpost', 'post')
			.replace('> ', ' ')
		},
		'languages': ['en'],
		'requestedAttributes': {},
	}

	for m in models:
		input_data['requestedAttributes'][m] = {}

	r = await s.post(
		perspective_url,
		json=input_data
	)
	raw_output = await r.json()
	try:
		models = raw_output['attributeScores'].keys()
	except KeyError:
		return {}

	output = {}
	raw_model_scores = raw_output['attributeScores']
	for model in models:
		output[model] = raw_model_scores[model]['summaryScore']['value']
	return output


def get_keyboard_smash_score(phrase):
	score = 0
	letter_pair_scores_tmp = letter_pair_scores
	for i in range(len(phrase) - 1):
		input_pair = phrase[i] + phrase[i + 1]
		score += letter_pair_scores_tmp.get(input_pair, 0)
		if input_pair in letter_pair_scores_tmp:
			del letter_pair_scores_tmp[input_pair]
	return score


def add_previous_message(message):
	global previous_user_messages
	if message.author.id not in previous_user_messages:
		previous_user_messages[message.author.id] = []
	previous_user_messages[message.author.id].append(message)


def get_previous_messages(member, last_seconds=3600):
	# get last 10 messages from user
	messages = []
	recent_message_count = 0

	now = datetime.now()
	for message in reversed(previous_user_messages.get(member.id, [])):
		if now - message.created_at < timedelta(seconds=last_seconds):
			messages.append(message)
		if now - message.created_at < timedelta(seconds=3600):
			recent_message_count += 1
	if recent_message_count == 0 and member.id in previous_user_messages:
		del previous_user_messages[member.id]
		return []
	return messages[:10]


async def check_repeat_spam(message):
	if message.content.startswith('!keyboardsmash '):
		return
	repeated_count = 0
	previous_messages = get_previous_messages(message.author, last_seconds=10)
	previous_messages.insert(0, message)
	total_keyboard_smash_score = 0
	spammiest_message_score = 0
	keyboard_smash_count = 0
	for previous_message in previous_messages[:5]:
		if not previous_message.content.startswith('!keyboardsmash '):
			keyboard_smash_score = get_keyboard_smash_score(previous_message.content)
			if keyboard_smash_score < spammiest_message_score:
				spammiest_message_score = keyboard_smash_score
			if keyboard_smash_score > 5:
				total_keyboard_smash_score += keyboard_smash_score * 3
				keyboard_smash_count += 1
			else:
				total_keyboard_smash_score += keyboard_smash_score
		if previous_message.content == message.content:
			repeated_count += 1
		else:
			break
	if repeated_count >= 3:
		return True
	if (total_keyboard_smash_score < -15 and keyboard_smash_count > 1) or total_keyboard_smash_score < -100:
		return True
	return False


async def check_spam(message):
	previous_messages = get_previous_messages(message.author, last_seconds=60)
	previous_messages.insert(0, message)
	same_message = True
	for previous_message in previous_messages[:4]:
		if message.content != previous_message.content:
			same_message = False
	if same_message and len(previous_messages) > 3:
		await message.delete()


async def get_perspectives_from_message(message):
	if message.content.strip() == '':
		return {}
	content = message.content
	for letter, regional_indicator in zip(
		'abcdefghijklmnopqrstuvwxyz',
		'🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿'
	):
		content = content.replace(regional_indicator, letter)
	content = unidecode.unidecode(content)
	scores = await get_perspective_score(content)
	if message.content.startswith('!toxicity '):
		scores['SEVERE_TOXICITY'] = 0

	return scores

invite_regex = re.compile(r'(discord\.gg|discordapp\.com\/invite|discord\.com\/invite|discord\.gg\/invite)\/(.{1,10})')


async def process_messsage(message, warn=True):
	# await process_for_invites(message)
	if message.channel.id == 719570596005937152:
		# Ignore spam channel
		return
	if message.channel.id == 735470150681100350:
		# Ignore skyblock threads
		return
	# Ignore your messages if you're already muted
	mute_remaining = int((await db.get_mute_end(message.author.id)) - time.time())
	if mute_remaining > 0:
		return
	content = message.content
	for letter, regional_indicator in zip(
		'abcdefghijklmnopqrstuvwxyz',
		'🇦🇧🇨🇩🇪🇫🇬🇭🇮🇯🇰🇱🇲🇳🇴🇵🇶🇷🇸🇹🇺🇻🇼🇽🇾🇿'
	):
		content = content.replace(regional_indicator, letter)
	content = content\
		.replace('Ⓜ', 'm')\
		.replace('🅰', 'a')\
		.replace('⭕', 'o')\
		.replace('🅾', 'o')\
		.replace('👁‍🗨', 'o')
	content = unidecode.unidecode(content)\
		.replace('Ⱡ', 'L')\
		.replace('Ỻ', 'lL')

	# antimoan
	if re.match(r'[\w\W]*[mM]+\W*[oO0Ⲟ⚪]+\W*[aA@]+\W*[nN]+[\w\W]*', content, flags=re.IGNORECASE):
		await message.delete()
		await discordbot.mute_user(
			message.author,
			15,
			message.guild.id if message.guild else None
		)
		return
	# antichilynn for someblanket and piglegs
	if message.author.id in {750815961942065252, 440574784271810572} and re.match(r'[\w\W]*c+[^a-z]*h+[^a-z]*[i1y]+[^a-z]*[li1]+[^a-z]*[yi]+[^a-z]*n+[\w\W]*', content, flags=re.IGNORECASE):
		await message.delete()
		await discordbot.mute_user(
			message.author,
			15,
			message.guild.id if message.guild else None
		)
		return

	if re.match(r'.*([1-2]?\d?\d)\.([1-2]?\d?\d)\.([1-2]?\d?\d)\.([1-2]?\d?\d).*', content):
		# 69.420.69.420
		await message.author.send('Don\'t post IP addresses in chat, nerd')
		await message.delete()
		await discordbot.mute_user(
			message.author,
			5,
			message.guild.id if message.guild else None
		)
		return

	await check_spam(message)

	perspectives = await get_perspectives_from_message(message)
	if not perspectives: return
	severe_toxicity = perspectives['SEVERE_TOXICITY']
	toxicity = perspectives['TOXICITY']
	identity_attack = perspectives['IDENTITY_ATTACK']

	if identity_attack > 0.85 and toxicity > 0.8 and severe_toxicity > 0.8:
		if time.time() - last_toxic_message_times.get(message.author.id, 0) < 3600:
			if time.time() - last_very_toxic_message_times.get(message.author.id, 0) < 3600 and identity_attack > 0.9:
				# if warn:
				# 	await message.channel.send(f'<@{message.author.id}>, please be nice. :rage:')
				await discordbot.mute_user(
					message.author,
					60 * 15,
					message.guild.id if message.guild else None
				)
			else:
				if identity_attack > 0.9:
					# if warn:
					# 	await message.channel.send(f'<@{message.author.id}>, please be nice. :rage:')
					await discordbot.mute_user(
						message.author,
						60 * 2,
						message.guild.id if message.guild else None
					)
				# else:
					# if warn:
					# 	await message.channel.send(f'<@{message.author.id}>, please be nice. :angry:')
				last_very_toxic_message_times[message.author.id] = time.time()
		else:
			# if warn:
			# 	await message.channel.send(f'<@{message.author.id}>, please be nice.')
			await discordbot.mute_user(
				message.author,
				15,
				message.guild.id if message.guild else None
			)
		last_toxic_message_times[message.author.id] = time.time()
		return

	if severe_toxicity and severe_toxicity > 0.8 and toxicity > 0.7:
		if time.time() - last_toxic_message_times.get(message.author.id, 0) < 3600:
			if time.time() - last_very_toxic_message_times.get(message.author.id, 0) < 3600 and severe_toxicity > 0.9:
				# if warn:
				# 	await message.channel.send(f'<@{message.author.id}>, please be nice. :rage:')
				await discordbot.mute_user(
					message.author,
					60 * 3,
					message.guild.id if message.guild else None
				)
			else:
				if severe_toxicity > 0.9:
					# if warn:
					# 	await message.channel.send(f'<@{message.author.id}>, please be nice. :rage:')
					await discordbot.mute_user(
						message.author,
						15,
						message.guild.id if message.guild else None
					)
				# else:
					# if warn:
					# 	await message.channel.send(f'<@{message.author.id}>, please be nice. :angry:')
				last_very_toxic_message_times[message.author.id] = time.time()
		# else:
			# if warn:
			# 	await message.channel.send(f'<@{message.author.id}>, please be nice.')
		last_toxic_message_times[message.author.id] = time.time()
		return

	add_previous_message(message)
