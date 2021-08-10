from forumsweats import db

name = 'setcounting'
aliases = ['setcounter']

async def run(message, value):
	if message.author.id != 856340031999311872: return
	await db.set_counter(message.guild.id, int(value))
	await message.channel.send('ok')
