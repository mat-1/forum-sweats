from ..gui import PaginationGUI

name = 'debuggui'
channels = ['bot-commands']


async def run(message):
	gui = PaginationGUI(
		title='Example GUI',
		options=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
	)
	await gui.make_message(
		client=message.client,
		user=message.author,
		channel=message.channel,
	)

	async for option in gui:
		await message.author.send(f'You selected **{option}**')
