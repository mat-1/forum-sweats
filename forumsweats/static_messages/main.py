from typing import List, Tuple
from forumsweats import db
import discord
import config
import os
import re

base_dir = 'forumsweats/static_messages'

def get_static_messages_in_folder() -> List[Tuple[int, str]]:
	files = os.listdir(base_dir)
	# remove all the files that aren't markdown or are the README
	relevant_files = [f for f in files if f.endswith('.md') and f != 'README.md']

	messages = []
	for file_name in relevant_files:
		with open(os.path.join(base_dir, file_name), 'r', encoding='utf8') as f:
			# get the channel id from config.channels
			channel_id = config.channels.get(file_name.split('.')[0])
			if not channel_id:
				print('No channel id found for file', file_name)
				continue
			messages.append((channel_id, f.read()))
	return messages

def split_discord_message(message: str):
	# Putting a `---` on a line will signify a separate message.
	# Putting text inside a comment `<!-- -->` won't make it show up in the actual Discord message.
	# If the comment is on its own line, the line is removed.
	# If adding a new line would make the message over 2000 characters, it will be split.
	split_messages = []
	current_message = ''
	message_without_comments = re.sub(r'(\n<!--.*?-->(?=\n))|(<!--.*?-->)', '', message)
	for line in message_without_comments.split('\n'):
		if line == '---':
			split_messages.append(current_message.strip())
			current_message = ''
		else:
			if len(current_message) + len(line) > 2000:
				split_messages.append(current_message.strip())
				current_message = line
			else:
				current_message += line + '\n'
	split_messages.append(current_message.strip())
	return split_messages


async def get_existing_static_message_ids():
	'''
	Returns a dictionary of channel ids mapped to the message ids
	'''
	return await db.get_static_messages(config.main_guild)

async def init(client: discord.Client):
	old_message_ids_dict = await get_existing_static_message_ids()
	print('old_message_ids_dict', old_message_ids_dict)
	new_message_ids_dict = {}

	messages = get_static_messages_in_folder()
	# send/update all the messages
	for static_message_channel_id, static_message_contents in messages:
		# get the discord channel
		channel = client.get_channel(static_message_channel_id)
		# make sure it's a text channel
		if not isinstance(channel, discord.TextChannel):
			continue

		# split the big message into several up to 2000 characters
		new_message_contents = split_discord_message(static_message_contents)

		# get the old ids of the message
		old_message_ids = old_message_ids_dict.get(str(static_message_channel_id), [])

		# get the old content of the message
		old_messages = []
		old_message_contents = []
		for old_message_id in old_message_ids:
			try:
				message = await channel.fetch_message(old_message_id)
			except:
				print('Warning: Could not fetch message', old_message_id, 'in channel', static_message_channel_id)
				continue
			old_messages.append(message)
			old_message_contents.append(message.content)

		# if the message hasn't actually changed, we don't need to do anything
		print(new_message_contents, old_message_contents)
		print(new_message_contents == old_message_contents)
		if new_message_contents == old_message_contents:
			new_message_ids_dict[str(static_message_channel_id)] = old_message_ids
			continue

		# delete the old messages
		try:
			await channel.delete_messages(old_messages)
		# if deleting the messages failed for whatever reason, delete them one by one
		except:
			for old_message in old_messages:
				try:
					await old_message.delete()
				except:
					pass

		# send the new messages
		new_message_ids = []
		for new_message_content in new_message_contents:
			new_message = await channel.send(new_message_content, allowed_mentions=discord.AllowedMentions.none())
			new_message_ids.append(new_message.id)
		new_message_ids_dict[str(static_message_channel_id)] = new_message_ids
		
	# update them in the database
	print('new_message_ids_dict', new_message_ids_dict)
	await db.set_static_messages(config.main_guild, new_message_ids_dict)
