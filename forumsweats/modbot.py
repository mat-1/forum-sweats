from discord import client
import config
from forumsweats import discordbot
from datetime import timedelta
from typing import Dict, List
from forumsweats import db
from .session import s
import unidecode
import discord
import time
import json
import os
import re

with open('letter_pairs.json', 'r') as f:
	letter_pair_scores = json.loads(f.read())
previous_user_messages: Dict[int, List[discord.Message]] = {}
last_toxic_message_times = {}
last_very_toxic_message_times = {}

perspective_key = os.getenv('perspective_key')
if not perspective_key:
	print('No perspective key found!')
perspective_url = (
	'https://commentanalyzer.googleapis.com/'
	f'v1alpha1/comments:analyze?key={perspective_key}'
) if perspective_key else None


async def get_perspective_score(message, models=['SEVERE_TOXICITY', 'TOXICITY', 'IDENTITY_ATTACK']):
	if not perspective_key or not perspective_url: return {}
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


def get_previous_messages(member: discord.User, last_seconds=3600):
	# get last 10 messages from user
	messages = []
	recent_message_count = 0

	now = discord.utils.utcnow()
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


async def check_spam(message) -> bool:
	if message.author.bot: return False
	previous_messages = get_previous_messages(message.author, last_seconds=60)
	previous_messages.insert(0, message)
	same_message = True
	for previous_message in previous_messages[:4]:
		if message.content != previous_message.content:
			same_message = False
	if same_message and len(previous_messages) > 3:
		await message.delete()
		return True
	return False


invite_regex = re.compile(r'(discord\.gg|discordapp\.com\/invite|discord\.com\/invite|discord\.gg\/invite)\/(.{1,10})')


async def process_message(message, warn=True, is_edit=False) -> bool:
	'''
	Process the message, returns True if the message was deleted
	'''

	if message.author.id == discordbot.client.user.id:
		return False

	content = message.content
	if not content and message.embeds and message.embeds[0].description and discordbot.client.user and message.author.id == discordbot.client.user.id:
		content = message.embeds[0].description

	if not isinstance(content, str):
		return False

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
		.replace('👁‍🗨', 'o')\
		.replace('ʒ', '3')\
		.replace('Ʒ', '3')

	content = unidecode.unidecode(content)\
		.replace('Ⱡ', 'L')\
		.replace('Ỻ', 'lL')\
		.replace('と', 'c')\
		.replace('€', 'c')\
		.replace('!', 'i')\
		.replace('3', 'e')\
		.replace('@', 'a')
	
	is_serious_talk = message.channel.id == config.channels.get('serious-talk')

	# antihoe for runic
	#if message.author.id == 617193050178977812 and re.match(r'[\w\W]*h(oe|œ|Œ)[\w\W]*', content, flags=re.IGNORECASE):
	#	await message.delete()
	#	await discordbot.mute_user(
	#		message.author,
	#		1,
	#		message.guild.id if message.guild else None,
	#	)
	#	return True

	# roger filters
	#if message.author.id == 621164650058219533 and re.match(r'[\w\W]*((w\W*h\W*(o|a)\W*r\W*e)|(h\W*e\W*n\W*t\W*a\W*i))[\w\W]*', content, flags=re.IGNORECASE):
	#	await message.delete()
	#	await discordbot.mute_user(
	#		message.author,
	#		1,
	#		message.guild.id if message.guild else None,
	#	)
	#	return True

	#if not is_serious_talk and re.search(r'\b[mM]+\W*[oO0Ⲟ⚪]+\W*[aA@]+\W*[nN]+([^a]|\b)', content, flags=re.IGNORECASE):
		#await message.delete()
		#await discordbot.mute_user(
			#message.author,
			#15,
			#message.guild.id if message.guild else None,
		#)
		#return True

	#if re.match(r'[\w\W]*\bc\W*u\W*m\b[\w\W]*', content, flags=re.IGNORECASE) or (not is_serious_talk and re.match(r'[\w\W]*\bs\W*p\W*e\W*r\W*m\b[\w\W]*', content, flags=re.IGNORECASE)):
		#await message.delete()
		#await discordbot.mute_user(
			#message.author,
			#60 * 5,
			#message.guild.id if message.guild else None,
		#)
		#return True

	if re.search(r'thiswordisblacklistedyouliterallycannotsayit', content, flags=re.IGNORECASE):
		await message.delete()
		try: await message.author.send('troll')
		except: pass
		return True
	

	# spam ping check
	mentioned_ids_unchecked = re.findall(r'<@[!&]?(\d{1,20})>', message.content)
	mentioned_ids = set()
	for id in mentioned_ids_unchecked:
		if (message.guild and message.guild.get_member(int(id))) or message.guild.get_role(int(id)):
			mentioned_ids.add(id)
	if len(mentioned_ids) >= 8:
		# delete, dm, and mute for a minute
		await message.delete()
		try:
			await message.author.send('Don\'t ping a lot of people at once, nerd')
		except:
			pass
		await discordbot.mute_user(
			message.author,
			60,
			message.guild.id if message.guild else None,
		)
		return True

	if not is_edit:
		is_spam = await check_spam(message)

		add_previous_message(message)

		return is_spam
	return False
