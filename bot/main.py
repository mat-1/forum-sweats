from dotenv import load_dotenv
load_dotenv()
from . import server, discordbot
import sys


print('starting')

server.start_server(
	discordbot.client.loop,
	discordbot.start_bot(),
	discordbot.client
)
