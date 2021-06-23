from forumsweats import modbot

name = 'toxicity'
args = '<message>'

async def run(message, check_message: str):
	'Tells you how toxic a certain message is'
	data = await modbot.get_perspective_score(check_message)
	score = data['SEVERE_TOXICITY']
	if 'hypixel' in check_message.lower() or 'skyblock' in check_message.lower() or 'the pit' in check_message.lower():
		score = 1
	await message.channel.send(f'Toxicity: {int(score*10000)/100}%')
