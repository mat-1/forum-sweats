from forumsweats import modbot
import discord
import re

name = 'morse'
args = '<message>'

letter_to_morse = {
	'a': '.-',
	'b': '-...',
	'c': '-.-.',
	'd': '-..',
	'e': '.',
	'f': '..-.',
	'g': '--.',
	'h': '....',
	'i': '..',
	'j': '.---',
	'k': '-.-',
	'l': '.-..',
	'm': '--',
	'n': '-.',
	'o': '---',
	'p': '.--.',
	'q': '--.-',
	'r': '.-.',
	's': '...',
	't': '-',
	'u': '..-',
	'v': '...-',
	'w': '.--',
	'x': '-..-',
	'y': '-.--',
	'z': '--..',
	'1': '.----',
	'2': '..---',
	'3': '...--',
	'4': '....-',
	'5': '.....',
	'6': '-....',
	'7': '--...',
	'8': '---..',
	'9': '----.',
	'0': '-----',
	',': '--..--',
	'.': '.-.-.-',
	'?': '..--..',
	'/': '-..-.',
	'-': '-....-',
	'(': '-.--.',
	')': '-.--.-'
}

morse_to_letter = {v: k for k, v in letter_to_morse.items()}

async def run(message: discord.Message, content: str=None):
	if not content:
		return await message.reply('Please provide morse code to decode or text to encode as morse code.')

	is_morse = re.match(r'^[.\- ]+$', content)

	# if it's morse, decode it
	if is_morse:
		decoded = ''
		for morse_sequence in content.split():
			try:
				decoded += morse_to_letter[morse_sequence]
			except KeyError:
				await message.reply('Invalid morse.')
		reply = await message.reply(
			embed=discord.Embed(
				title='Decoded morse',
				description=decoded
			)
		)
	else:
		# if it's not morse, encode it
		encoded = ''
		for letter in content:
			encoded += letter_to_morse[letter.lower()] + ' '
		reply = await message.reply(
			embed=discord.Embed(
				title='Encoded morse',
				description=encoded
			)
		)
	
	print('reply', reply.embeds)

	try:
		if await modbot.process_message(reply, False):
			await message.delete()
	except:
		pass

