from ..commandparser import Member

name = 'avatar'

async def run(message, member: Member):
	'Gets the Discord avatar for a member'
	await message.channel.send(str(
		member.avatar_url_as(format='gif')
		if member.is_avatar_animated()
		else member.avatar_url_as(format='png')
	))

