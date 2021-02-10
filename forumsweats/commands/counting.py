from forumsweats import db

name = 'counting'
aliases = ['counter']


async def run(message, value):
	counter = await db.get_counter(message.guild.id)
	await message.channel.send(counter)
