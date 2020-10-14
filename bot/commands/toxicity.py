import modbot
name = 'toxicity'


async def run(message, check_message: str):
	data = await modbot.get_perspective_score(check_message)
	score = data['SEVERE_TOXICITY']
	await message.channel.send(f'Severe toxicity: {int(score*10000)/100}%')
