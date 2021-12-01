import aiohttp
import asyncio

s: Optional[aiohttp.ClientSession] = None


async def init():
	global s
	s = aiohttp.ClientSession()
	# has to be in an async function or else aiohttp gets mad



loop = asyncio.get_event_loop()

# init on startup
loop.run_until_complete(init())
