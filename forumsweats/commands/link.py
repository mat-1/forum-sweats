from forumsweats import db, hypixel
from utils import get_role_id
import discord
import time


name = 'link'
args = '<ign>'


async def run(message, ign: str = None):
	'Links your Discord account to your Minecraft account and gives you your rank roles'
	if not ign:
		return await message.send(
			'Do `!link yourusername` to link to your Hypixel account.'
		)
	ign = ign.strip()
	try:
		data = await hypixel.get_user_data(ign)
		try:
			discord_name = data.get('player', {}).get('socials', {}).get('discord')
			assert discord_name is not None
		except AssertionError:
			raise hypixel.DiscordNotFound()
	except hypixel.PlayerNotFound:
		return await message.send('Invalid username.')
	except hypixel.DiscordNotFound:
		return await message.send(
			"You haven't set your Discord username in Hypixel yet."
		)
	if str(message.author) == discord_name:
		pass  # good
	else:
		error_message = (
			'Incorrect username. Did you link your account correctly in Hypixel? '
			f'({ign} is linked to {discord_name})'
		)
		return await message.send(embed=discord.Embed(
			description=error_message
		))

	old_rank = await db.get_hypixel_rank(message.author.id)
	new_rank = await hypixel.get_hypixel_rank(ign)

	new_rank_role_id = None

	# Give the user their rank in all servers
	for guild in message.client.guilds:
		member = guild.get_member(message.author.id)
		if not member:
			# Member isn't in the guild
			continue

		# Remove the user's old rank
		if old_rank:
			old_rank_role_id = get_role_id(guild.id, old_rank)
			if old_rank_role_id:
				old_rank_role = guild.get_role(old_rank_role_id)
				await member.remove_roles(old_rank_role, reason='Old rank')

		new_rank = data['rank']
		new_rank_role_id = get_role_id(guild.id, new_rank)
		if new_rank_role_id:
			new_rank_role = guild.get_role(new_rank_role_id)
			await member.add_roles(new_rank_role, reason='Update rank')

	await db.set_hypixel_rank(message.author.id, new_rank)
	await db.set_minecraft_ign(message.author.id, ign, data['uuid'])

	if new_rank_role_id:
		await message.channel.send(
			embed=discord.Embed(
				description=(
					f'Linked your account to **{ign}** '
					f'and updated your role to **{new_rank}**.'
				)
			)
		)
	else:
		await message.channel.send(
			embed=discord.Embed(
				description=f'Linked your account to **{ign}**.'
			)
		)

	# If you're muted, stop running the function
	mute_end = await db.get_mute_end(message.author.id)
	if (mute_end and mute_end > time.time()):
		return

	# You're already verified, stop running the function
	is_member = await db.get_is_member(message.author.id)
	if is_member:
		return

	for guild in message.client.guilds:
		member = guild.get_member(message.author.id)
		if not member:
			# Member isn't in the guild
			continue
		member_role_id = get_role_id(guild.id, 'member')
		member_role = guild.get_role(member_role_id)
		await member.add_roles(member_role, reason='New member linked')
	await db.set_is_member(message.author.id)
