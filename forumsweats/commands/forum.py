name = 'forum'
aliases = ('forums', 'f')
pad_none = False


async def run(message):
	await message.send('Forum commands: **!forums user (username)**')
