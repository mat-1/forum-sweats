from forumsweats import db

name = 'counting'
aliases = ('counter', 'count', 'getcounting', 'getcounter')


async def run(message):
	'Tells you the current value of the number in <#738449805218676737>'
	counter = await db.get_counter(message.guild.id)
	await message.channel.send(counter)
