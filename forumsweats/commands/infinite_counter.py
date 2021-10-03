from forumsweats import db

name = 'infinite-counting'
aliases = (
	'inf-count', 'inf-counting', 'inf-counter', 'infinite-count', 'infinite-counter',
	'infinitecounting', 'infcount', 'infcounting', 'infcounter', 'infinitecount', 'infinitecounter')


async def run(message):
	'Tells you the current value of the number in <#816898842179403817>'
	counter = await db.get_infinite_counter(message.guild.id)
	await message.channel.send(counter)
