name = 'stackdandelion'
aliases = ['stackdandelions', 'fixdandelionstacking']

fix_dandelion_stacking_fixed = False


async def run(message):
	global fix_dandelion_stacking_fixed
	if not fix_dandelion_stacking_fixed:
		await message.send('Dandelion stacking has been fixed.')
	else:
		await message.send('Dandelion stacking is now broken again.')
	fix_dandelion_stacking_fixed = not fix_dandelion_stacking_fixed
