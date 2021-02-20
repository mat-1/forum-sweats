import asyncio
from ..gui import PaginationGUI, TextGUI

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
	# option = await gui.wait_for_option()

	async for option in gui:
		await message.author.send(f'You selected **{option}**')
