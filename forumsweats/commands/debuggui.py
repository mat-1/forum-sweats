from ..gui import PaginationGUI

name = 'debuggui'
channels = ['bot-commands']


async def run(message):
	gui = PaginationGUI(
		message.client,
		user=message.author,
		channel=message.channel,
		title='Example GUI',
		options=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
	)
	await gui.make_message()
	async for option in gui:
		print(option)
		await message.send(option)
