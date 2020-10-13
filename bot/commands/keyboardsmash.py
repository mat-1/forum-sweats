import modbot

name = 'keyboardsmash'


async def run(message, check_message: str):
	score = modbot.get_keyboard_smash_score(check_message)
	await message.channel.send(f'Score: {score}')
