name = 'membercount'
aliases = ['members']


async def run(message):
	'Lists the number of people that are in this server'
	true_member_count = message.guild.member_count
	await message.channel.send(
		f'There are **{true_member_count:,}** people in this server.'
	)
