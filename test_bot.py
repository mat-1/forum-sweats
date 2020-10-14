from dotenv import load_dotenv
load_dotenv()
import bot.discordbot as bot
import discordpytest
import pytest
import asyncio

print('starting')

@pytest.fixture
def test():
	return discordpytest.Tester(bot.client)


@pytest.fixture
def client(test):
	return test.client


@pytest.fixture
def guild(test):
	return test.make_guild(id=1)


@pytest.fixture
def channel(test, guild):
	return test.make_channel(1, id=2)


@pytest.mark.asyncio
async def test_e(test, channel):
	await test.message('!e', channel)
	test.verify_message('e')

# bot.client.loop.run_until_complete(test_e(channel(guild())))