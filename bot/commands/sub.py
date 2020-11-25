from bot.betterbot import Member
from bot import confirmgui
import discord
import db

name = 'sub'
aliases = ['simp', 'bobuxsub', 'subscribe', 'bobuxsubscribe', 'bobuxsimp']


tiers = {
	't1': 20,
	't2': 80,
	't3': 200
}


async def verify_required_bobux(member, tier):
	tier_cost = tiers[tier]
	bobux = await db.get_bobux(member.id)
	# If you have at least the required amount of bobux to sub for a week,
	return bobux >= tier_cost


async def subscribe(user, subbing_to, tier):
	await db.bobux_subscribe_to(user.id, subbing_to.id, tier)


async def run(message, member: Member = None, tier: str = None):
	if not member:
		return await message.channel.send('Invalid member.')
	if not tier:
		return await message.channel.send('No tier specified (must be t1-t3).')
	tier = tier.lower()
	if tier not in tiers:
		return await message.channel.send('Invalid tier (must be t1-t3).')

	if not await verify_required_bobux(message.author, tier):
		return await message.channel.send(f'You don\'t have enough bobux to {tier} sub')

	tier_cost = tiers[tier]

	verify_message = await message.channel.send(embed=discord.Embed(
		description=f'Are you sure you want to **{tier}** sub to {member.mention} by sending **{tier_cost}** bobux per week?'
	))
	confirmed = await confirmgui.make_confirmation_gui(message.client, verify_message, message.author)

	if not await verify_required_bobux(message.author, tier):
		# Check again in case they sent bobux while the confirmation was active or something
		return await message.channel.send(f'You don\'t have enough bobux to {tier} sub')

	if confirmed:
		await subscribe(message.author, member, tier)
		await verify_message.edit(embed=discord.Embed(
			description=f'Subbed to {member.mention}!'
		))
	else:
		await verify_message.edit(embed=discord.Embed(
			description=f'Cancelled sub to {member.mention}!'
		))
