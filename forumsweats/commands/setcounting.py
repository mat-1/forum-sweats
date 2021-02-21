from forumsweats import db

name = 'setcounting'
aliases = ['setcounter']

async def run(message, value):
	if message.author.id != 224588823898619905: return
	await db.set_counter(message.guild.id, int(value))
	await message.channel.send('ok')
