from ..commandparser import Member

name = 'avatar'

async def run(message, member: Member):
	'Gets the Discord avatar for a member'
	await message.channel.send(member.avatar_url)
