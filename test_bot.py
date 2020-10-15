import bot.discordbot as bot
import discordpytest
import pytest


@pytest.fixture
def test():
	tester = discordpytest.Tester(bot.client)
	bot.client = tester.client
	return tester


@pytest.fixture
def client(test):
	return test.client


@pytest.fixture
def guild(test):
	return test.make_guild(id=717904501692170260)


@pytest.fixture
def channel(test, guild):
	return test.make_channel(guild, id=718076311150788649)


@pytest.mark.asyncio
async def test_e(test, channel):
	await test.message('!e', channel)
	await test.verify_message('e')


@pytest.mark.asyncio
async def test_forum(test, channel):
	await test.message('!forum', channel)
	await test.verify_message('Forum commands: **!forums user (username)**')


# @pytest.mark.asyncio
# async def test_forum_user(test, channel):
# 	await test.message('!forum user matdoesdev', channel)
# 	await test.verify_message(lambda m: m['embed']['title'] == 'matdoesdev\'s forum stats', timeout=15)


@pytest.mark.asyncio
async def test_debugmember(client, test, channel, guild):
	user_1 = test.make_member(guild, test.make_user(1, 'mat', 1234))
	user_2 = test.make_member(guild, test.make_user(2, 'matdoesdev', 4321))
	user_3 = test.make_member(guild, test.make_user(3, 'gaming', 1234))
	user_2 = test.make_member(guild, test.make_user(4, 'mat does dev', 4321))
	await test.message('!debugmember mat', channel)
	await test.verify_message(lambda m: m['embed']['description'] == '<@1>')

	await test.message('!debugmember matdoesdev', channel)
	await test.verify_message(lambda m: m['embed']['description'] == '<@2>')

	await test.message('!debugmember mat does dev', channel)
	await test.verify_message(lambda m: m['embed']['description'] == '<@4>')

	await test.message('!debugmember mat d', channel)
	await test.verify_message(lambda m: m['embed']['description'] == '<@4>')

	await test.message('!debugmember matd', channel)
	await test.verify_message(lambda m: m['embed']['description'] == '<@2>')

	await test.message('!debugmember mat#1234', channel)
	await test.verify_message(lambda m: m['embed']['description'] == '<@1>')

	await test.message('!debugmember m#1234', channel)
	await test.verify_message('Unknown member')

	await test.message('!debugmember Mat', channel)
	await test.verify_message(lambda m: m['embed']['description'] == '<@1>')

	await test.message('!debugmember MATDOESDE', channel)
	await test.verify_message(lambda m: m['embed']['description'] == '<@2>')

	await test.message('!debugmember g', channel)
	await test.verify_message(lambda m: m['embed']['description'] == '<@3>')
