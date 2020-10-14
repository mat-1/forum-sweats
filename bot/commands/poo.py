name = 'poo'
aliases = ['poop']
bot_channel = False


async def run(message):
	'poops in gulag'

	if message.channel.id != 720073985412562975: return
	await message.channel.send('You have pooped.')
