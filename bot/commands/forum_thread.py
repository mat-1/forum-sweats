from utils import trim_string
import discord
import forums
import time

name = 'forum'
aliases = ['forums', 'f']
pad_none = False
channels = None


forum_ratelimit = {}


def check_forum_ratelimit(user):
	global forum_ratelimit
	if user not in forum_ratelimit: return False
	user_ratelimit = forum_ratelimit[user]
	last_minute_uses = 0
	last_10_second_uses = 0
	last_3_second_uses = 0
	for ratelimit in user_ratelimit:
		if time.time() - ratelimit < 60:
			last_minute_uses += 1
			if time.time() - ratelimit < 10:
				last_10_second_uses += 1
				if time.time() - ratelimit < 10:
					last_3_second_uses += 1
		else:
			del user_ratelimit[0]
	if last_minute_uses >= 10: return True
	if last_10_second_uses >= 3: return True
	if last_3_second_uses >= 2: return True
	return False


def add_forum_ratelimit(user):
	global forum_ratelimit
	if user not in forum_ratelimit:
		forum_ratelimit[user] = []
	forum_ratelimit[user].append(time.time())


async def run(message, command, thread_id: int):
	if command not in {
		'post',
		'thread',
	}:
		raise TypeError

	if check_forum_ratelimit(message.author.id):
		return await message.send('Stop spamming the command, nerd')
	add_forum_ratelimit(message.author.id)

	print('ok')
	async with message.channel.typing():
		thread = await forums.get_thread(thread_id)
		if not thread:
			return await message.send('Invalid thread.')
		body_trimmed = trim_string(thread['body'])
		embed = discord.Embed(
			title=thread['title'],
			description=body_trimmed,
			url=thread['url']
		)
		embed.set_author(
			name=thread['author']['name'],
			url=thread['author']['url'],
			icon_url=thread['author']['avatar_url'],
		)
		if thread['image']:
			embed['image'] = {
				'url': thread['image']
			}
		await message.channel.send(embed=embed)
