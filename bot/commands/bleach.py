import discord

name = 'bleach'


async def run(message):
	embed = discord.Embed(
		title='Here\'s a Clorox bleach if you want to unsee something weird:'
	)
	embed.set_image(
		url='https://cdn.discordapp.com/attachments/741200821936586785/741200842430087209/Icon_3.jpg'
	)
	await message.channel.send(embed=embed)
