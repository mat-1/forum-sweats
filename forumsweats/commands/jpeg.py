from ..commandparser import Context, Member
from typing import Optional
from ..session import s
import discord
import aiohttp

name = 'jpeg'
args = '[member]'
aliases = ('jpg',)

s: Optional[aiohttp.ClientSession] = None

async def upload(im_bytes, content_type):
	data = aiohttp.FormData()
	data.add_field(
		'image',
		im_bytes,
		content_type=content_type
	)
	if not s: return None
	async with s.post(
		'https://jpeg.repl.co',
		data=data,
	) as r:
		new_url = str(r.url)
	if content_type == 'image/gif':
		new_url = new_url + '.gif'
	return new_url


async def run(message: Context, item: str=None):
	'Compresses an image. A lot.'

	if not s:
		return await message.reply('Bot seems to still be initializing, please wait a few seconds and try again.')

	image_url: str
	image_content_type: str

	if item:
		member = await Member.convert(Member, message, item) # type: ignore usually pylance gives a warning when we put Member as self
	else:
		member = None

	async with message.channel.typing():
		# first, try to get the image from the member avatar
		# if that doesn't work, check if it starts with https:// or http:// and if so get the url from that
		# finally, check if there's an image attached
		# if all that fails just gives an error
		if member:
			img_size = 128
			user = message.client.get_user(member.id)
			if not user:
				return await message.reply('User not found.')
			asset = user.display_avatar.with_static_format('png').with_size(img_size)
			image_url = str(asset)
		elif item is not None and (item.startswith('https://') or item.startswith('http://')):
			image_url = str(item)
		elif message.attachments:
			image_url = message.attachments[0].url
		else:
			return await message.reply('Please provide an image or member to jpeg when using the command.')


		r = await s.get(image_url)
		im_bytes = await r.read()
		image_content_type = r.headers['content-type'].split(';')[0]

		url = await upload(im_bytes, image_content_type)

		if not url:
			return await message.reply('Upload failed, maybe try again in a few minutes?')

		embed = discord.Embed(title='JPEG')

		embed.set_image(url=url)

		await message.reply(embed=embed)
