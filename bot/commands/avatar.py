from ..betterbot import Member

name = 'avatar'
description = 'Gets the Discord avatar for a member'

async def run(message, member: Member):
	await message.channel.send(member.avatar_url)
