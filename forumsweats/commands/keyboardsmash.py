from forumsweats import modbot

name = 'keyboardsmash'
args = '<message>'

async def run(message, check_message: str):
	'Tells you how likely it is that a message is spam from a user smashing their keyboard.'
	score = modbot.get_keyboard_smash_score(check_message)
	await message.channel.send(f'Score: {score}')
