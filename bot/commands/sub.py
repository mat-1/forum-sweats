from bot.betterbot import Member
from bot import confirmgui
import discord

name = 'sub'
aliases = ['simp', 'bobuxsub', 'subscribe', 'bobuxsubscribe', 'bobuxsimp']


tiers = {
	't1': 20,
	't2': 80,
	't3': 200
}


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
	print('ok making gui')
	confirmed = await confirmgui.make_confirmation_gui(message.client, verify_message, message.author)

	if confirmed:
		await verify_message.edit(embed=discord.Embed(
			description=f'Subbed to {member.mention}!'
		))
	else:
		await verify_message.edit(embed=discord.Embed(
			description=f'Cancelled sub to to {member.mention}!'
		))
