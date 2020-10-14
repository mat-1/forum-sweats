from ..discordbot import has_role
from ..betterbot import Member
import db

name = 'givebobux'
bot_channel = False


async def run(message, member: Member = None, amount: int = 0):
	if not has_role(message.author.id, 717904501692170260, 'admin'): return
	if not member:
		return await message.channel.send('invalid member')
	if not amount:
		return await message.channel.send('invalid amount')
	await db.change_bobux(member.id, amount)
	await message.channel.send('ok')
