from ..betterbot import Member
import discord

name = 'sub'
aliases = ['simp', 'bobuxsub', 'subscribe', 'bobuxsubscribe', 'bobuxsimp']


tiers = {
	't1': 20,
	't2': 80,
	't3': 200
}

agree_reaction = '✅'
disagree_reaction = '❌'


async def run(message, member: Member = None, tier: str = None):
	if not member:
		return await message.channel.send('Invalid member.')
	if not tier:
		return await message.channel.send('No tier specified (must be t1-t3).')
	tier = tier.lower()
	if tier not in tiers:
		return await message.channel.send('Invalid tier (must be t1-t3).')

	tier_cost = tiers[tier]

	verify_message = await message.channel.send(embed=discord.Embed(
		description=f'Are you sure you want to **{tier}** sub to {member.mention} by sending **{tier_cost}** bobux per week?'
	))
	await verify_message.add_reaction(agree_reaction)
	await verify_message.add_reaction(disagree_reaction)

	def check(reaction, user):
		if user != message.author: return False
		if reaction.emoji != agree_reaction and reaction.emoji != disagree_reaction: return False
		if reaction.message != verify_message: return False
		return True
	reaction, user = await message.client.wait_for('reaction_add', check=check)
	print(reaction, user)
