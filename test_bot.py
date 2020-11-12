import bot.discordbot as bot
import discordpytest
import asyncio
import pytest
import time
import db

bobux_queue = []


async def fake_change_bobux(user_id: int, amount: int):
	global bobux_queue
	bobux_queue.append({
		'user_id': user_id,
		'amount': amount
	})


async def get_mute_end(user_id: int):
	return 0


async def get_counter(guild_id: int):
	return 1


db.change_bobux = fake_change_bobux
db.get_mute_end = get_mute_end
db.get_counter = get_counter


async def verify_bobux(checker, timeout=1):
	global bobux_queue
	started_time = time.time()

	while len(bobux_queue) == 0:
		await asyncio.sleep(0)
		elapsed_time = time.time() - started_time
		if elapsed_time > timeout:
			raise TimeoutError()
	assert checker(bobux_queue.pop())


@pytest.fixture
def test():
	tester = discordpytest.Tester(bot.client)
	bot.client.http = tester.client.http
	bot.client._connection = tester.client._connection
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


@pytest.mark.asyncio
async def test_duel_general_win(client, test):
	guild = test.make_guild(id=717904501692170260)
	general = test.make_channel(guild, id=719579620931797002)
	user = test.make_member(guild, test.make_user(1, 'mat', 6207))
	print('doing message')
	await test.message('!duel <@719348452491919401>', general, user)
	await test.verify_message(
		'<@719348452491919401>, react to this message with :gun: to duel <@1>. '
		'The loser will get muted for one hour'
	)
	await test.verify_message('Duel starting in 10 seconds... First person to type :gun: once the countdown ends, wins.')
	await test.verify_message('5')
	await test.verify_message('4')
	await test.verify_message('3')
	await test.verify_message('2')
	await test.verify_message('1')
	await test.verify_message('Shoot')
	await asyncio.sleep(0)
	await test.message(':gun:', general, user)
	await test.verify_message('<@1> won the duel!')


@pytest.mark.asyncio
async def test_counter(client, test, channel):
	await test.message('!counter', channel)
	await test.verify_message('1')
