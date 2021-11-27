from typing import Optional
import discord
import config

def create_log_embed(member: discord.Member, moderator: discord.Member, description: str, color: discord.Color):
	embed = discord.Embed(
		description=description,
		color=color
	)
	embed.set_author(
		icon_url=member.display_avatar.url,
		name=str(member)
	)
	embed.set_footer(
		text=f'By {str(moderator)} ({moderator.id})',
		icon_url=moderator.display_avatar.url
	)
	return embed

async def send_log(client: discord.Client, channel_id: int, member: discord.Member, moderator: discord.Member, reason: str, color: discord.Color):
	'''
	Log a message to one of the log channels.
	'''
	embed = create_log_embed(member, moderator, reason, color)
	guild = client.get_guild(config.main_guild)

	# if the guild doesn't exist, return
	if guild is None:
		return

	log_channel = guild.get_channel(channel_id)

	# if the channel isn't a text channel, return
	if not isinstance(log_channel, discord.TextChannel):
		return

	await log_channel.send(embed=embed)



async def log_mute(client: discord.Client, member: discord.Member, moderator: discord.Member, time: int, reason: Optional[str]):
	# we import this here to avoid circular imports
	from forumsweats.commands.mute import create_mute_message

	await send_log(
		client=client,
		channel_id=config.channels['public-mod-logs'],
		member=member,
		moderator=moderator,
		reason=create_mute_message(member, time, reason),
		color=discord.Color.from_rgb(255, 0, 0)
	)

async def log_unmute(client: discord.Client, member: discord.Member, moderator: discord.Member, reason: Optional[str]):
	# we import this here to avoid circular imports
	from forumsweats.commands.unmute import create_unmute_message

	await send_log(
		client=client,
		channel_id=config.channels['public-mod-logs'],
		member=member,
		moderator=moderator,
		reason=create_unmute_message(member, reason),
		color=discord.Color.red()
	)

async def log_warn(client: discord.Client, member: discord.Member, moderator: discord.Member, reason: str):
	from forumsweats.commands.warn import create_warn_message
	await send_log(
		client=client,
		channel_id=config.channels['public-mod-logs'],
		member=member,
		moderator=moderator,
		reason=create_warn_message(member, reason),
		color=discord.Color.yellow()
	)
