import forumsweats.discordbot as bot
from asyncio.queues import Queue
from forumsweats import db
import discordpytest
import asyncio
import pytest
import config
import time
import json

bobux_queue = []

db.connection_url = None


async def fake_change_bobux(user_id: int, amount: int):
	global bobux_queue
	bobux_queue.append({
		'user_id': user_id,
		'amount': amount
	})
db.change_bobux = fake_change_bobux


async def get_mute_end(user_id: int):
	return 0
db.get_mute_end = get_mute_end


counter = 1
@pytest.fixture(autouse=True)
def reset_counter():
	global counter
	counter = 1

async def get_counter(guild_id: int):
	return counter
db.get_counter = get_counter

async def set_counter(guild_id: int, value: int):
	global counter
	counter = value
db.set_counter = set_counter

async def get_active_reminders():
	return []
db.get_active_reminders = get_active_reminders

async def get_activity_bobux(user_id: int):
	# these user ids are considered new members
	if user_id == 533502154191798273 or user_id == 533502154191798274:
		return 0
	return 200
db.get_activity_bobux = get_activity_bobux






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
	bot.client._connection._ready_state = Queue(0)
	return tester


@pytest.fixture
def client(test):
	return test.client


@pytest.fixture
def guild(test):
	return test.make_guild(id=config.main_guild)

def get_channel_from_config(channel_name: str) -> int:
	channel = config.channels.get(channel_name, [])
	return channel[0]

@pytest.fixture
def channel(test: discordpytest.Tester, guild):
	return test.make_channel(guild, id=get_channel_from_config('bot-commands'))

@pytest.fixture
def counting_channel(test: discordpytest.Tester, guild):
	return test.make_channel(guild, id=get_channel_from_config('counting'))

@pytest.mark.asyncio
async def test_avatar(test: discordpytest.Tester, channel, guild):
	user_1 = test.make_member(
		guild, test.make_user(1, 'mat', '1234', avatar='asdf'))
	await test.message('!avatar mat', channel)
	await test.verify_message(lambda m: m['content'].startswith('https://cdn.discordapp.com/avatars/1/asdf.'))


@pytest.mark.asyncio
async def test_b(test: discordpytest.Tester, channel):
	await test.message('!b', channel)
	await test.verify_message('I like french bread')


@pytest.mark.asyncio
async def test_bleach(test: discordpytest.Tester, channel):
	await test.message('!bleach', channel)
	await test.verify_message(
		lambda m: m['embeds'][0].get('title') == 'Here\'s a Clorox bleach if you want to unsee something weird:'
	)


# @pytest.mark.asyncio
# async def test_bobux(test: discordpytest.Tester, channel):
# 	await test.message('!bobux', channel)


@pytest.mark.asyncio
async def test_e(test: discordpytest.Tester, channel):
	await test.message('!e', channel)
	await test.verify_message('e')


@pytest.mark.asyncio
async def test_forum(test: discordpytest.Tester, channel):
	await test.message('!forum', channel)
	await test.verify_message('Forum commands: **!forums user (username)**')


@pytest.mark.asyncio
async def test_debugmember(client, test: discordpytest.Tester, channel, guild):
	user_1 = test.make_member(guild, test.make_user(1, 'mat', '1234'))
	user_2 = test.make_member(guild, test.make_user(2, 'matdoesdev', '4321'))
	user_3 = test.make_member(guild, test.make_user(3, 'gaming', '1234'))
	user_2 = test.make_member(guild, test.make_user(4, 'mat does dev', '4321'))

	await test.message('!debugmember mat', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description') == '<@1>')

	await test.message('!debugmember matdoesdev', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description') == '<@2>')

	await test.message('!debugmember mat does dev', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description') == '<@4>')

	await test.message('!debugmember mat d', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description') == '<@4>')

	await test.message('!debugmember matd', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description') == '<@2>')

	await test.message('!debugmember mat#1234', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description') == '<@1>')

	await test.message('!debugmember m#1234', channel)
	await test.verify_message('Unknown member')

	await test.message('!debugmember Mat', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description') == '<@1>')

	await test.message('!debugmember MATDOESDE', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description') == '<@2>')

	await test.message('!debugmember g', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description') == '<@3>')


@pytest.mark.asyncio
async def test_debugtime(client, test: discordpytest.Tester, channel):
	time_tests = {
		'1 second': '1 second',
		'2 seconds': '2 seconds',
		'59 seconds': '59 seconds',
		'1s': '1 second',
		'1seconds': '1 second',
		'30	seconds': '30 seconds',
		'60 seconds': '1 minute',
		'599seconds': '9 minutes and 59 seconds',
		'3600s': '1 hour',

		'1 minute': '1 minute',
		'2 minutes': '2 minutes',
		'59 minute': '59 minutes',
		'61m': '1 hour and 1 minute',
	}
	for test_input in time_tests:
		test_expected_output = time_tests[test_input]
		await test.message(f'!debugtime {test_input}', channel)
		await test.verify_message(test_expected_output)


@pytest.mark.asyncio
async def test_duel_general_win(client, test):
	guild = test.make_guild(id=config.main_guild)
	general = test.make_channel(guild, id=config.channels['general'])
	user = test.make_member(guild, test.make_user(1, 'mat', '6207'))
	await test.message('!duel <@719348452491919401>', general, user)
	await test.verify_message(
		lambda m: m['content'].startswith('<@719348452491919401>, react to this message with :gun: to duel <@1>.')
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
async def test_counter(client, test: discordpytest.Tester, channel):
	await test.message('!counter', channel)
	await test.verify_message('1')


@pytest.mark.asyncio
async def test_counting(client, test: discordpytest.Tester, guild, counting_channel):
	new_member = test.make_member(guild, test.make_user(533502154191798273, 'Otty', '5345'))
	other_new_member = test.make_member(guild, test.make_user(533502154191798274, 'alt', '9999'))

	member = test.make_member(guild, test.make_user(999999999999999999, 'mat', '0001'))
	other_member = test.make_member(guild, test.make_user(999999999999999999, 'duck', '0001'))

	# make sure new members can count correct numbers
	m = await test.message('2', counting_channel, new_member)
	await test.verify_reaction_added(lambda r: r['emoji'] == bot.COUNTING_CONFIRMATION_EMOJI and str(r['message_id']) == str(m['id']))

	# make sure normal members can still count
	m = await test.message('3', counting_channel, member)
	await test.verify_reaction_added(lambda r: r['emoji'] == bot.COUNTING_CONFIRMATION_EMOJI and str(r['message_id']) == str(m['id']))

	# make sure new members can't count the wrong number
	m = await test.message('troll', counting_channel, other_new_member)
	await test.verify_message_deleted(int(m['id']))


	# make sure old members can still count the wrong number
	test.clear_queues()
	m = await test.message('troll', counting_channel, other_member)
	await test.verify_message(lambda m: m['content'].startswith(f'<@{other_member.id}> put an invalid number and ruined it for everyone'))

@pytest.mark.asyncio
async def test_filter(client, test: discordpytest.Tester, channel):
	m = await test.message('th¡swordisblacklistʒdyoulitƷrallycannotsayit', channel)
	await test.verify_message_deleted(int(m['id']))

@pytest.mark.asyncio
async def test_spamping(client, test: discordpytest.Tester, guild, channel):
	test.make_member(guild, test.make_user(11, 'one', '0001'))
	test.make_member(guild, test.make_user(12, 'two', '0002'))
	test.make_member(guild, test.make_user(13, 'three', '0003'))
	test.make_member(guild, test.make_user(14, 'four', '0004'))
	test.make_member(guild, test.make_user(15, 'five', '0005'))
	test.make_member(guild, test.make_user(16, 'six', '0006'))
	test.make_member(guild, test.make_user(17, 'seven', '0007'))
	test.make_member(guild, test.make_user(18, 'eight', '0008'))
	test.make_member(guild, test.make_user(19, 'nine', '0009'))
	test.make_member(guild, test.make_user(110, 'ten', '0010'))

	m = await test.message('<@11> <@12> <@13> <@14> <@15> <@16> <@17> <@18> <@19> <@110>', channel)
	await test.verify_message_deleted(int(m['id']))

@pytest.mark.asyncio
async def test_morse(client, test: discordpytest.Tester, channel):
	await test.message('!morse .... . .-.. .-.. ---', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description') == 'hello')

	await test.message('!morse hello', channel)
	await test.verify_message(lambda m: m['embeds'][0].get('description', '').strip() == '.... . .-.. .-.. ---')

	# thiswordisblacklistedyouliterallycannotsayit
	m = await test.message('!morse - .... .. ... .-- --- .-. -.. .. ... -... .-.. .- -.-. -.- .-.. .. ... - . -.. -.-- --- ..- .-.. .. - . .-. .- .-.. .-.. -.-- -.-. .- -. -. --- - ... .- -.-- .. -', channel)
	await test.verify_message_deleted(int(m['id']))

@pytest.mark.asyncio
async def test_help(client, test: discordpytest.Tester, channel):
	await test.message('!help', channel)
	await test.verify_message(
		lambda m:
			len(m['embeds']) > 0
			and m['embeds'][0].get('footer', {}).get('text', '').startswith('(Page 1/')
	)

	await test.message('!help 2', channel)
	await test.verify_message(
		lambda m:
			len(m['embeds']) > 0
			and m['embeds'][0].get('footer', {}).get('text', '').startswith('(Page 2/')
	)

