from ..commandparser import Member

name = 'avatar'

async def run(message, member: Member):
	'Gets the Discord avatar for a member'
	
	if not member:
		member = message.author
		
	await message.channel.send(str(
		member.avatar.with_format('gif')
		if member.avatar.is_animated()
		else member.avatar.with_format('png')
	))

