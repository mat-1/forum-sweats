import asyncio
import os
if not os.getenv('token'):
	from dotenv import load_dotenv
	load_dotenv()
from . import server, discordbot


print('Starting')

asyncio.run(server.start_server(
	discordbot.client.loop,
	discordbot.start_bot,
	discordbot.client
))
