from forumsweats.betterbot import Member
from forumsweats import confirmgui
import discord
from forumsweats import db

name = 'sub'
aliases = ['simp', 'bobuxsub', 'subscribe', 'bobuxsubscribe', 'bobuxsimp']


tiers = {
	't1': 20,
	't2': 80,
	't3': 200
}


async def is_subbed(subber, subbee):
	subs = await db.bobux_get_subscriptions(subber.id)
	for sub in subs:
		if sub['id'] == subbee.id:
			return True
	return False


async def verify_required_bobux(member, tier):
	tier_cost = tiers[tier]
	bobux = await db.get_bobux(member.id)
	# Check that you have at least the required amount of bobux to sub for a week
	return bobux >= tier_cost


async def subscribe(user, subbing_to, tier):
	user_id = user.id if hasattr(user, 'id') else int(user)
	subbing_to_id = subbing_to.id if hasattr(subbing_to, 'id') else int(subbing_to)

	tier_cost = tiers[tier]
	await db.change_bobux(user_id, -tier_cost)
	await db.change_bobux(subbing_to_id, tier_cost)
	await db.bobux_subscribe_to(user_id, subbing_to_id, tier)


async def run(message, member: Member = None, tier: str = None):
	if not member:
		return await message.channel.send('Invalid member.')
	if not tier:
		return await message.channel.send('No tier specified (must be t1-t3).')
	tier = tier.lower()
	if tier not in tiers:
		return await message.channel.send('Invalid tier (must be t1-t3).')

	if await is_subbed(message.author, member):
		return await message.channel.send(
			'You\'re already subbed to this member. Unsub and resub if you\'d like to change your sub tier.'
		)

	subs = await db.bobux_get_subscriptions(message.author.id)
	if len(subs) >= 25:
		return await message.channel.send(
			'You\'re subbed to too many people! Use !subs to check who you\'re subbed to, '
			'and !unsub <member> to unsubscribe from them'
		)

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

	edited_content = None

	if confirmed:
		if await is_subbed(message.author, member):
			edited_content = f'You\'re already subbed to {member.mention}'
		else:
			await subscribe(message.author, member, tier)
			edited_content = f'Subbed to {member.mention}!'
	else:
		edited_content = f'Cancelled sub to {member.mention}!'
	await verify_message.edit(embed=discord.Embed(
		description=edited_content
	))
