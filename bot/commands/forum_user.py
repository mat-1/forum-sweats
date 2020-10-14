import discord
import forums
import time

# !forum user
name = 'forum'
aliases = ['forums', 'f']
pad_none = False


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


async def run(message, command, user):
	if command not in {
		'member',
		'user',
	}:
		raise TypeError

	if check_forum_ratelimit(message.author.id):
		return await message.send('Stop spamming the command, nerd')
	add_forum_ratelimit(message.author.id)

	async with message.channel.typing():
		member_id = await forums.member_id_from_name(user)
		if not member_id:
			return await message.send('Invalid user.')
		print('member_id', member_id)
		member = await forums.get_member(member_id)

		total_messages = member['messages']
		follower_count = member.get('follower_count')
		positive_reactions = member['reactions']['positive_total']
		member_name = member['name']
		member_id = member['id']
		avatar_url = member['avatar_url']

		description = (
			f'Messages: {total_messages:,}\n'
			+ (f'Followers: {follower_count:,}\n' if follower_count is not None else '')
			+ f'Reactions: {positive_reactions:,}\n'
		)

		embed = discord.Embed(
			title=f"{member_name}'s forum stats",
			description=description,
			url=f'https://hypixel.net/members/{member_id}/'
		)

		if follower_count is None:
			embed.set_footer(text='This member limits who may view their full profile.')

		embed.set_thumbnail(url=avatar_url)

		await message.channel.send(embed=embed)
