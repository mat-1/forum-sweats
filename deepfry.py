import aiohttp

async def upload(im_bytes, content_type):
	data = aiohttp.FormData()
	data.add_field('image',
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
