from ..betterbot import Time
from ..discordbot import mute_user
import time
from forumsweats import db


name = 'gulag'


async def run(message, length_time: Time = Time(60)):
	'Mutes you for one minute'
	mute_remaining = int((await db.get_mute_end(message.author.id)) - time.time())
	if mute_remaining > 0:
		return await message.send('You are already in gulag')
	if length_time < 60:
		return await message.send('You must be in gulag for at least 60 seconds')
	if length_time > 60 * 15:
		return await message.send('You can only be in gulag for up to 15 minutes')
	length = int(length_time)
	if length // 60 > 1:
		await message.send(f'You have entered gulag for {length // 60} minutes.')
	else:
		await message.send(f'You have entered gulag for {length} seconds.')

	await mute_user(
		message.author,
		length,
		message.guild.id if message.guild else None
	)
