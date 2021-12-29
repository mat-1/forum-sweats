from forumsweats import db, discordbot
from forumsweats import numberparser
from ..commandparser import Member
import re

name = 'givesocialcredit'
aliases = (
	'addsocialcredit', 'givesocialcredits', 'addsocialcredits',
	'addsc', 'givesc'
)
roles = ('mod', 'admin', 'xijinping')
args = '[member]'
channels = None

social_credit_message_re = re.compile(r'^([+-])(.+?) social credits?$')

async def run(message, member: Member = None, amount: int = None, reason: str=None):
	if not member or not amount:
		return await message.reply(f'Invalid member or amount')
	social_credit = await db.change_social_credit(member.id, amount) + 1000
	if amount > 0:
		await message.channel.send(f'<@{member.id}>, you have earned **{amount}** social credit. You now have a total of {social_credit} social credit.')
	else:
		await message.channel.send(f'<@{member.id}>, you have lost **{-amount}** social credit. You now have a total of {social_credit} social credit.')

async def process_message(message):
	if not message.reference:
		return

	# if the user doesn't have any of the roles, return
	if not any(discordbot.has_role(message.author.id, role) for role in roles):
		return
	
	# now, check if the message matches "+/- [amount] social credit"
	match = social_credit_message_re.match(message.content)
	if not match:
		return

	sign = match.group(1)
	number_string = match.group(2)
	number = numberparser.solve_expression(number_string.strip())

	if number is None:
		return

	if sign == '-':
		number = -number
	
	number = int(number)

	if message.reference.resolved:
		await run(message, message.reference.resolved.author, number)



