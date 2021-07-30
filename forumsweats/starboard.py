from typing import Union
from .discordbot import client
from . import db
import discord
import config

# change this if you want your starboard to use a different emoji
STAR_EMOJI = '⭐'
# you need at least this amount of stars for the message to get sent
STAR_REQUIREMENT = 5
# whether the user starring their own message counts towards the total star count
ALLOW_SELF_STAR = False

async def get_star_count(message: discord.Message):
	star_count = 0
	for reaction in message.reactions:
		if reaction.emoji == STAR_EMOJI:
			if ALLOW_SELF_STAR:
				star_count += reaction.count
			else:
				async for user in reaction.users():
					if user != message.author:
						star_count += 1
	return star_count

async def add_message_to_starboard(message: discord.Message):
	starboard_channel = client.get_channel(config.channels['starboard'])
	if not starboard_channel: return

	star_count = await get_star_count(message)

	# if the message doesnt have enough stars, return
	if star_count < STAR_REQUIREMENT:
		return


	message_content = message.content
	if not isinstance(message_content, str):
		message_content = ''

	if len(message.embeds) > 0:
		try:
			message_content += '\n' + message.embeds[0].description
		except:
			pass

	embed = discord.Embed(
		title=f'{STAR_EMOJI} {star_count} stars',
		description=message_content,
	)
	embed.set_author(
		name=str(message.author),
		icon_url=message.author.avatar.url,
		url=message.jump_url
	)
	if len(message.attachments) > 0:
		# we can do this to quickly check if its an image
		if message.attachments[0].width:
			embed.set_image(url=message.attachments[0].url)
			extra_attachments = message.attachments[1:]
		else:
			extra_attachments = message.attachments
		if len(extra_attachments) > 0:
			for attachment in extra_attachments:
				embed.description += '\n' + attachment.url
		
	
	embed.add_field(name='Link', value=f'[Click to go to message]({message.jump_url})')

	existing_starboard_message = await db.fetch_starboard_message(message.id)
	existing_starboard_message_id = existing_starboard_message.get('starboard_message_id')

	if existing_starboard_message_id:
		# message already exists in starboard!
		existing_message: discord.Message = await starboard_channel.fetch_message(existing_starboard_message_id)
		await existing_message.edit(content=None, embed=embed)
	else:
		existing_starboard_message = await starboard_channel.send(embed=embed)
		existing_starboard_message_id = existing_starboard_message.id

	await db.add_starboard_message(message.id, existing_starboard_message_id, star_count)


async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
	# if there's no starboard channel in config, return
	if not config.channels['starboard']:
		return

	# if the guild id is different, return
	if payload.guild_id != config.main_guild:
		return

	# you can't star messages already in #starboard
	if payload.channel_id == config.channels['starboard']:
		return
	
	channel: Union[discord.abc.Messageable, None] = client.get_channel(payload.channel_id)

	# if the channel doesnt exist for some reason, return
	if not channel: return

	message = await channel.fetch_message(payload.message_id)

	await add_message_to_starboard(message)
