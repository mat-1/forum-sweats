from forumsweats import db

name = 'setcounting'
aliases = ['setcounter']
roles = ('admin',)

async def run(message, value):
	await db.set_counter(message.guild.id, int(value))
	await message.channel.send('ok')
