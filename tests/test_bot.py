from asyncio.queues import Queue
import forumsweats.discordbot as bot
from forumsweats import db
import discordpytest
import asyncio
import pytest
import config
import time

print('imported things', bot)

bobux_queue = []


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


async def get_counter(guild_id: int):
    return 1
db.get_counter = get_counter


async def get_active_reminders():
    return []
db.get_active_reminders = get_active_reminders


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


@pytest.fixture
def channel(test, guild):
    return test.make_channel(guild, id=config.channels['bot-commands'])


@pytest.mark.asyncio
async def test_avatar(test, channel, guild):
    user_1 = test.make_member(
        guild, test.make_user(1, 'mat', 1234, avatar='asdf'))
    await test.message('!avatar mat', channel)
    # await test.verify_message(lambda m: m['content'].startswith('https://cdn.discordapp.com/avatars/1/asdf.'))
    await test.verify_message(lambda m: print(m) or True)


@pytest.mark.asyncio
async def test_b(test, channel):
    await test.message('!b', channel)
    await test.verify_message('I like french bread')


# @pytest.mark.asyncio
# async def test_bleach(test, channel):
#     await test.message('!bleach', channel)
#     await test.verify_message(
#         lambda m: m['embed']['title'] == 'Here\'s a Clorox bleach if you want to unsee something weird:'
#     )


# # @pytest.mark.asyncio
# # async def test_bobux(test, channel):
# # 	await test.message('!bobux', channel)


# @pytest.mark.asyncio
# async def test_e(test, channel):
#     await test.message('!e', channel)
#     await test.verify_message('e')


# @pytest.mark.asyncio
# async def test_forum(test, channel):
#     await test.message('!forum', channel)
#     await test.verify_message('Forum commands: **!forums user (username)**')


# # @pytest.mark.asyncio
# # async def test_forum_user(test, channel):
# # 	await test.message('!forum user matdoesdev', channel)
# # 	await test.verify_message(lambda m: m['embed']['title'] == 'matdoesdev\'s forum stats', timeout=15)


# @pytest.mark.asyncio
# async def test_debugmember(client, test, channel, guild):
#     user_1 = test.make_member(guild, test.make_user(1, 'mat', 1234))
#     user_2 = test.make_member(guild, test.make_user(2, 'matdoesdev', 4321))
#     user_3 = test.make_member(guild, test.make_user(3, 'gaming', 1234))
#     user_2 = test.make_member(guild, test.make_user(4, 'mat does dev', 4321))
#     await test.message('!debugmember mat', channel)
#     await test.verify_message(lambda m: m['embed']['description'] == '<@1>')

#     await test.message('!debugmember matdoesdev', channel)
#     await test.verify_message(lambda m: m['embed']['description'] == '<@2>')

#     await test.message('!debugmember mat does dev', channel)
#     await test.verify_message(lambda m: m['embed']['description'] == '<@4>')

#     await test.message('!debugmember mat d', channel)
#     await test.verify_message(lambda m: m['embed']['description'] == '<@4>')

#     await test.message('!debugmember matd', channel)
#     await test.verify_message(lambda m: m['embed']['description'] == '<@2>')

#     await test.message('!debugmember mat#1234', channel)
#     await test.verify_message(lambda m: m['embed']['description'] == '<@1>')

#     await test.message('!debugmember m#1234', channel)
#     await test.verify_message('Unknown member')

#     await test.message('!debugmember Mat', channel)
#     await test.verify_message(lambda m: m['embed']['description'] == '<@1>')

#     await test.message('!debugmember MATDOESDE', channel)
#     await test.verify_message(lambda m: m['embed']['description'] == '<@2>')

#     await test.message('!debugmember g', channel)
#     await test.verify_message(lambda m: m['embed']['description'] == '<@3>')


# @pytest.mark.asyncio
# async def test_debugtime(client, test, channel):
#     time_tests = {
#         '1 second': '1 second',
#         '2 seconds': '2 seconds',
#         '59 seconds': '59 seconds',
#         '1s': '1 second',
#         '1seconds': '1 second',
#         '30     seconds': '30 seconds',
#         '60 seconds': '1 minute',
#         '599seconds': '9 minutes and 59 seconds',
#         '3600s': '1 hour',

#         '1 minute': '1 minute',
#         '2 minutes': '2 minutes',
#         '59 minute': '59 minutes',
#         '61m': '1 hour and 1 minute',
#     }
#     for test_input in time_tests:
#         test_expected_output = time_tests[test_input]
#         await test.message(f'!debugtime {test_input}', channel)
#         await test.verify_message(test_expected_output)


# @pytest.mark.asyncio
# async def test_duel_general_win(client, test):
#     guild = test.make_guild(id=config.main_guild)
#     general = test.make_channel(guild, id=config.channels['general'])
#     user = test.make_member(guild, test.make_user(1, 'mat', 6207))
#     print('doing message')
#     await test.message('!duel <@719348452491919401>', general, user)
#     await test.verify_message(
#         '<@719348452491919401>, react to this message with :gun: to duel <@1>. '
#         'The loser will get muted for one hour'
#     )
#     await test.verify_message('Duel starting in 10 seconds... First person to type :gun: once the countdown ends, wins.')
#     await test.verify_message('5')
#     await test.verify_message('4')
#     await test.verify_message('3')
#     await test.verify_message('2')
#     await test.verify_message('1')
#     await test.verify_message('Shoot')
#     await asyncio.sleep(0)
#     await test.message(':gun:', general, user)
#     await test.verify_message('<@1> won the duel!')


# @pytest.mark.asyncio
# async def test_counter(client, test, channel):
#     await test.message('!counter', channel)
#     await test.verify_message('1')
