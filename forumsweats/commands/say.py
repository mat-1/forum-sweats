from forumsweats.commandparser import Context


name = 'say'
roles = ('mod', 'helper')
channels = None
args = ''

async def run(message: Context):
    await message.channel.send(message.content[len(name) + 1:])
    await message.delete()