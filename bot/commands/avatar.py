from ..betterbot import Member

name = 'avatar'


async def run(message, member: Member):
	await message.channel.send(member.avatar_url)
