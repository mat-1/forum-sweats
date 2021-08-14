from ..commandparser import Member
from forumsweats import db

name = 'removesocialcredit'
aliases = ('takesocialcredit',)
roles = ('mod', 'admin')
args = '[member]'


async def run(message, member: Member = None, amount: int = None):
	if not member or not amount:
		return await message.reply(f'Invalid member or amount')
	amount = amount - 1
	social_credit = await db.change_social_credit(member.id, amount)
	if amount > 0:
		await message.channel.send(f'@<{member.id}>, you have earned **{amount}** social credit. You now have a total of {social_credit} social credit.')
	else:
		await message.channel.send(f'@<{member.id}>, you have lost **{amount}** social credit. You now have a total of {social_credit} social credit.')
