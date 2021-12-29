from ..commandparser import Member
from forumsweats import db

name = 'givesocialcredit'
aliases = (
	'addsocialcredit', 'givesocialcredits', 'addsocialcredits',
	'addsc', 'givesc'
)
roles = ('mod', 'admin', 'xijinping')
args = '[member]'
channels = None


async def run(message, member: Member = None, amount: int = None, reason: str=None):
	if not member or not amount:
		return await message.reply(f'Invalid member or amount')
	social_credit = await db.change_social_credit(member.id, amount) + 1000
	if amount > 0:
		await message.channel.send(f'<@{member.id}>, you have earned **{amount}** social credit. You now have a total of {social_credit} social credit.')
	else:
		await message.channel.send(f'<@{member.id}>, you have lost **{-amount}** social credit. You now have a total of {social_credit} social credit.')
