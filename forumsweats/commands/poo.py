name = 'poo'
aliases = ['poop']
channels = ['gulag']


async def run(message):
	'poops in gulag'

	await message.channel.send('You have pooped.')
