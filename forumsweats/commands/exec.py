from contextlib import redirect_stdout
import traceback
import discord
import io

name = 'exec'
aliases = ('eval',)
channels = None


def execute(_code, loc):  # Executes code asynchronously
	_code = _code.replace('\n', '\n ')
	globs = globals()
	globs.update(loc)
	exec(
		'async def __ex():\n ' + _code,
		globs
	)
	return globs['__ex']()


async def run(message, code: str):
	if message.author.id != 224588823898619905: return
	f = io.StringIO()
	with redirect_stdout(f):
		command = message.content.split(None, 1)[1].strip()
		if command.startswith('```') and command.endswith('```'):
			command = '\n'.join(command.split('\n')[1:])
			command = command[:-3]
		try:
			output = await execute(command, locals())
		except Exception as e:
			traceback.print_exc()
	out = f.getvalue()
	if out == '':
		# out = 'No output.'
		return
	await message.send(
		embed=discord.Embed(
			title='Eval',
			description=out
		)
	)
