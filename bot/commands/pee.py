name = 'pee'
bot_channel = False


async def run(message):
	'pees in gulag'

	if message.channel.id != 720073985412562975: return
	await message.channel.send('You have peed.')
