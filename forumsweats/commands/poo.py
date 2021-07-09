name = 'poo'
aliases = ['poop']
channels = ['gulag']


async def run(message):
	await message.channel.send('You have pooped.')
