import discord

agree_reaction = '✅'
disagree_reaction = '❌'


async def make_confirmation_gui(client, message, user):
	print('make_confirmation_gui', message)
	await message.add_reaction(agree_reaction)
	await message.add_reaction(disagree_reaction)

	def check(reaction, check_user):
		if user.id != check_user.id: return False
		if reaction.emoji != agree_reaction and reaction.emoji != disagree_reaction: return False
		if reaction.message.id != message.id: return False
		return True

	reaction, user = await client.wait_for('reaction_add', check=check)
	try:
		await message.clear_reactions()
	except discord.Forbidden:
		pass
	return reaction.emoji == agree_reaction
