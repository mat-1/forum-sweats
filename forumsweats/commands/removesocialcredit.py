from ..commandparser import Member
from forumsweats import db

name = 'removesocialcredit'
aliases = ('takesocialcredit', 'removesocialcredits', 'takesocialcredits', 'subtractsocialcredits', 'subtractsocialcredit')
roles = ('mod', 'admin')
args = '[member]'
channels = None


async def run(message, member: Member = None, amount: int = None):
	if not member or not amount:
		return await message.reply(f'Invalid member or amount')
	amount = -amount
	social_credit = await db.change_social_credit(member.id, amount) + 1000
	if amount > 0:
		await message.channel.send(f'<@{member.id}>, you have earned **{amount}** social credit. You now have a total of {social_credit} social credit.')
	else:
		await message.channel.send(f'<@{member.id}>, you have lost **{amount}** social credit. You now have a total of {social_credit} social credit.')
