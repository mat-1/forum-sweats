from ..commandparser import Member
import discord
import io
import aiohttp

name = 'jpeg'
args = '[member]'

async def upload(im_bytes, content_type):
	data = aiohttp.FormData()
	data.add_field(
		'image',
		im_bytes,
		content_type=content_type
	)
	async with aiohttp.ClientSession() as s:
		async with s.post(
			'https://jpeg.repl.co',
			data=data,
		) as r:
			new_url = str(r.url)
	if content_type == 'image/gif':
		new_url = new_url + '.gif'
	return new_url


async def run(message, member: Member):
	'Compresses a user\'s avatar. A lot.'
	async with message.channel.typing():
		img_size = 128
		user = message.client.get_user(member.id)
		with io.BytesIO() as output:
			asset = user.avatar_url_as(static_format='png', size=img_size)
			await asset.save(output)
			if '.gif' in asset._url:
				content_type = 'image/gif'
			else:
				content_type = 'image/png'
			output.seek(0)
			img_bytes = output.getvalue()

		url = await upload(img_bytes, content_type)

	embed = discord.Embed(title='JPEG')

	embed.set_image(url=url)

	await message.channel.send(embed=embed)
