from ..commandparser import Member

name = 'avatar'

async def run(message, member: Member = None):
	'Gets the Discord avatar for a member'
	
	if not member:
		member = message.author
		
	await message.channel.send(str(
		member.display_avatar.with_format('gif')
		if member.avatar.is_animated()
		else member.display_avatar.with_format('png')
	))

