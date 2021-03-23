from forumsweats.commands.giveaway import end_giveaway
from forumsweats.commandparser import Context
from forumsweats import db


name = 'reroll'
roles = ('mod',)
channels = None
args = '<message id>'

async def run(message: Context, giveaway_id_str: str):
	try:
		giveaway_id = int(giveaway_id_str)
	except:
		return await message.send('Invalid message id.')
	giveaway_data = await db.get_giveaway(giveaway_id)

	if giveaway_data is None:
		return await message.send('Couldn\'t find a giveaway with that id.')

	if not giveaway_data['ended']:
		return await message.send('That giveaway hasn\'t ended yet.')

	await end_giveaway(giveaway_data)
	await message.add_reaction('👍')
	