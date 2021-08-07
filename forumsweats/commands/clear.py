from forumsweats import confirmgui


name = 'clear'
aliases = ('purge',)
args = '<amount>'
channels = None
roles = ('helper',)


async def run(message, amount_str: str):
	'Purge recent messages'

	try:
		amount = int(amount_str)
	except:
		return await message.reply('Invalid amount')

	if amount >= 1000:
		return await message.reply('You can\'t clear this many messages.')

	if amount >= 50:
		verify_message = await message.reply(f'Are you sure you want to purge {amount} recent messages?')
		confirmed = await confirmgui.make_confirmation_gui(message.client, verify_message, message.author)
		if not confirmed:
			return
		# add 1 to include this new message
		amount += 1

	await message.channel.purge(limit=amount)
