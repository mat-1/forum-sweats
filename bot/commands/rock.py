from ..discordbot import mute_user
from ..betterbot import Member
import time
import db

name = 'rock'
aliases = ['stone']
bot_channel = False


async def run(message, member: Member):
	"Adds 5 minutes to someone's mute in gulag"

	if message.channel.id not in {
		720073985412562975,  # gulag
		718076311150788649,  # bot-commands
	}: return

	if not member:
		return await message.send('Unknown member. Example usage: **!rock pigsty**')

	if member == message.author.id:
		return await message.send("You can't throw a rock at yourself.")

	mute_end = await db.get_mute_end(member.id)
	if not (mute_end and mute_end > time.time()):
		return await message.send('This person is not in gulag.')
	mute_remaining = mute_end - time.time()

	print('mute_remaining')

	# makes sure people havent thrown a rock in the last hour
	last_rock_thrown = await db.get_rock(message.author.id)

	if time.time() - last_rock_thrown < 60 * 60:
		# TODO: Make this use seconds_to_string in utils
		next_rock_seconds = (60 * 60) - int(time.time() - last_rock_thrown)
		next_rock_minutes = next_rock_seconds // 60
		if next_rock_minutes >= 2:
			next_rock_str = f'{next_rock_minutes} minutes'
		elif next_rock_minutes == 1:
			next_rock_str = 'one minute'
		elif next_rock_seconds == 1:
			next_rock_str = 'one second'
		else:
			next_rock_str = f'{next_rock_seconds} seconds'
		return await message.send(
			f'You threw a rock too recently. You can throw a rock again in {next_rock_str}'
		)

	bobux = await db.get_bobux(message.author.id)
	if bobux < 2:
		return await message.send('You need at least 2 bobux to use !rock')
	await db.change_bobux(message.author.id, -2)

	await db.set_rock(message.author.id)

	# Add 5 minutes to someone's mute
	has_bigger_rock = await db.spend_shop_item(message.author.id, 'bigger_rock')
	if has_bigger_rock:
		rock_length = 60 * 10
	else:
		rock_length = 60 * 5
	new_mute_remaining = int(mute_remaining + rock_length)

	print('muting again')

	new_mute_remaining_minutes = int(new_mute_remaining // 60)
	new_mute_remaining_hours = int(new_mute_remaining_minutes // 60)
	if new_mute_remaining_hours >= 2:
		new_mute_str = f'{new_mute_remaining_hours} hours'
	elif new_mute_remaining_hours == 1:
		new_mute_str = 'one hour'
	elif new_mute_remaining_minutes >= 2:
		new_mute_str = f'{new_mute_remaining_minutes} minutes'
	elif new_mute_remaining_minutes == 1:
		new_mute_str = 'one minute'
	elif new_mute_remaining == 1:
		new_mute_str = 'one second'
	else:
		new_mute_str = f'{new_mute_remaining} seconds'
	await message.send(f'<@{member.id}> is now muted for {new_mute_str}')

	await mute_user(
		member,
		new_mute_remaining,
		717904501692170260
	)
