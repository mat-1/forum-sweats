from ..betterbot import Time
from .utils import seconds_to_string

name = 'debugtime'


async def run(message, length: Time):
	'Debugging command seconds_to_string test time'
	await message.send(seconds_to_string(length))
