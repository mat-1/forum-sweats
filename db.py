import motor.motor_asyncio
import os
import time
import uuid
from datetime import datetime, timedelta

connection_url = os.getenv('dburi')

client = motor.motor_asyncio.AsyncIOMotorClient(connection_url)

db = client.discord

member_data = db['members']
infractions_data = db['infractions']
servers_data = db['servers']


async def set_minecraft_ign(user_id, ign, uuid):
	if not connection_url: return
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': {
				'minecraft': {
					'ign': ign,
					'uuid': uuid
				}
			}
		},
		upsert=True
	)


async def get_minecraft_data(user_id):
	if not connection_url: return
	data = await member_data.find_one({
		'discord': user_id,
	})
	if data:
		return data.get('minecraft')


async def set_hypixel_rank(user_id, rank):
	if not connection_url: return
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': {
				'hypixel_rank': rank
			}
		},
		upsert=True
	)


async def get_hypixel_rank(user_id):
	if not connection_url: return
	data = await member_data.find_one({
		'discord': user_id,
	})
	if data:
		return data.get('hypixel_rank')


async def set_mute_end(user_id, end_time, extra_data={}):
	if not connection_url: return
	set_data = {
		'muted_until': end_time
	}
	for data in extra_data:
		set_data[f'muted_data.{data}'] = extra_data[data]
	set_data['muted'] = end_time > time.time()
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': set_data
		},
		upsert=True
	)


async def get_is_muted(user_id):
	if not connection_url: return
	data = await member_data.find_one(
		{
			'discord': int(user_id)
		}
	)
	if data:
		return data.get('muted', False)
	else:
		return 0


async def get_mute_end(user_id):
	if not connection_url: return 0
	data = await member_data.find_one(
		{
			'discord': int(user_id)
		}
	)
	if data:
		return data.get('muted_until', 0)
	else:
		return 0


async def get_mute_data(user_id):
	if not connection_url: return {}
	data = await member_data.find_one(
		{
			'discord': int(user_id)
		}
	)
	if data:
		return data.get('muted_data', {})
	else:
		return 0


async def get_active_mutes():
	if not connection_url: return
	active_mutes = {}
	async for member in member_data.find(
		{
			'muted_until': {
				'$gte': time.time()
			}
		}
	):
		active_mutes[member['discord']] = member['muted_until']
	return active_mutes


async def add_infraction(user_id: int, infraction_type, reason, mute_length=0):
	if not connection_url: return
	infraction_uuid = str(uuid.uuid4())
	await infractions_data.insert_one({
		'_id': infraction_uuid,
		'user': user_id,
		'type': infraction_type,
		'reason': reason,
		'date': datetime.now(),
		'length': str(mute_length)  # must be a string otherwise mongodb gets mad on long mutes
	})


async def get_infractions(user_id: int):
	if not connection_url: return
	infractions = []
	async for infraction in infractions_data.find({
		'user': user_id,
		'date': {'$gt': datetime.now() - timedelta(days=30)}
	}):
		infractions.append(infraction)
	return infractions


async def clear_infractions(user_id: int, date):
	if not connection_url: return
	r = await infractions_data.delete_many({
		'user': user_id,
		'date': {
			'$gte': date,
			'$lte': date + timedelta(days=1),
		}
	})
	return r.deleted_count


async def clear_recent_infraction(user_id: int):
	if not connection_url: return
	async for infraction in infractions_data\
		.find({'user': user_id})\
		.sort('date', -1)\
		.limit(1):
		await clear_infraction(infraction['_id'])


async def clear_infraction(infraction_id):
	await infractions_data.delete_one({'_id': infraction_id})


async def clear_infraction_by_partial_id(infraction_partial_id):
	infraction_data = await infractions_data.find_one({'_id': {
		'$regex': '^' + infraction_partial_id + '.*'
	}})
	if not infraction_data: return None
	await infractions_data.delete_one({'_id': infraction_data['_id']})
	return infraction_data


async def set_rock(user_id: int):
	if not connection_url: return
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': {
				'last_rock': time.time()
			}
		},
		upsert=True
	)


async def get_rock(user_id: int):
	if not connection_url: return
	data = await member_data.find_one(
		{
			'discord': int(user_id)
		}
	)
	if data:
		return data.get('last_rock', 0)
	else:
		return 0


async def add_message(user_id: int):
	if not connection_url: return
	hour_id = int(time.time() / 3600)
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$inc': {
				f'messages.{hour_id}': 1
			}
		},
		upsert=True
	)


async def get_active_members_from_past_hour(hoursago=1):
	if not connection_url: return
	hour_id = int((time.time()) / 3600) - hoursago
	members = []
	async for member in member_data.find(
		{
			f'messages.{hour_id}': {'$gte': 1}
		}
	):
		print('bruh', member, hour_id)
		member_modified = member
		member_modified['hourly_messages'] = member['messages'].get(str(hour_id), 0)
		del member_modified['messages']
		members.append(member_modified)
	return members


async def set_is_member(user_id: int):
	if not connection_url: return
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': {
				'member': True
			}
		},
		upsert=True
	)


async def get_is_member(user_id: int):
	if not connection_url: return
	data = await member_data.find_one(
		{
			'discord': int(user_id)
		}
	)
	if data:
		return data.get('member', False)
	else:
		return 0


async def set_counter(guild_id: int, number: int):
	if not connection_url: return
	await servers_data.update_one(
		{
			'id': guild_id
		},
		{
			'$set': {
				'counter': number
			}
		},
		upsert=True
	)


async def get_counter(guild_id: int):
	if not connection_url: return
	data = await servers_data.find_one({
		'id': guild_id,
	})
	if data:
		return data.get('counter', 0)


async def set_last_general_duel(guild_id: int):
	if not connection_url: return
	await servers_data.update_one(
		{
			'id': guild_id
		},
		{
			'$set': {
				'last_duel': datetime.now()
			}
		},
		upsert=True
	)


async def get_last_general_duel(guild_id: int):
	if not connection_url: return
	data = await servers_data.find_one({
		'id': guild_id,
	})
	if data:
		return data.get('last_duel')


async def set_bobux(user_id: int, amount: int):
	if not connection_url: return
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': {
				'bobux': amount
			}
		},
		upsert=True
	)


async def get_bobux(user_id: int):
	if not connection_url: return
	data = await member_data.find_one(
		{
			'discord': user_id
		}
	)
	return data.get('bobux', 0)


async def change_bobux(user_id: int, amount: int):
	if not connection_url: return
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$inc': {
				'bobux': amount
			}
		},
		upsert=True
	)


async def get_shop_item(user_id: int, shop_item_id: str):
	if not connection_url: return
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': {
				f'shop.{shop_item_id}': True
			}
		},
		upsert=True
	)


async def get_bought_shop_items(user_id: int):
	if not connection_url: return
	data = await member_data.find_one(
		{
			'discord': user_id
		}
	)
	shop_items = set()
	for item in data.get('shop', {}):
		if data['shop'][item]:
			shop_items.add(item)
	return shop_items


async def has_shop_item(user_id: int, shop_item_id: str):
	if not connection_url: return
	shop_items = await get_bought_shop_items(user_id)
	return shop_item_id in shop_items


async def spend_shop_item(user_id: int, shop_item_id: str):
	has_item = await has_shop_item(user_id, shop_item_id)
	if has_item:
		await lose_shop_item(user_id, shop_item_id)
	return has_item


async def lose_shop_item(user_id: int, shop_item_id: str):
	if not connection_url: return
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': {
				f'shop.{shop_item_id}': False
			}
		},
		upsert=True
	)


async def set_moot_end(user_id, end_time, extra_data={}):
	if not connection_url: return
	set_data = {
		'mooted_until': end_time
	}
	for data in extra_data:
		set_data[f'mooted_data.{data}'] = extra_data[data]
	set_data['mooted'] = end_time > time.time()
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': set_data
		},
		upsert=True
	)


async def get_is_mooted(user_id):
	if not connection_url: return
	data = await member_data.find_one(
		{
			'discord': int(user_id)
		}
	)
	if data:
		return data.get('mooted', False)
	else:
		return 0


async def get_mooted_end(user_id):
	if not connection_url: return 0
	data = await member_data.find_one(
		{
			'discord': int(user_id)
		}
	)
	if data:
		return data.get('mooted_until', 0)
	else:
		return 0


async def get_moot_data(user_id):
	if not connection_url: return {}
	data = await member_data.find_one(
		{
			'discord': int(user_id)
		}
	)
	if data:
		return data.get('mooted_data', {})
	else:
		return 0


async def get_moot_end(user_id):
	if not connection_url: return 0
	data = await member_data.find_one(
		{
			'discord': int(user_id)
		}
	)
	if data:
		return data.get('muted_until', 0)
	else:
		return 0


async def get_bobux_leaderboard(limit=10):
	leaderboard = []
	async for member in member_data\
		.find({'bobux': {'$gte': 1}})\
		.sort('bobux', -1)\
		.limit(limit):
		leaderboard.append(member)
	return leaderboard


async def bobux_subscribe_to(user_id, subbing_to_id, tier):
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': {
				f'subs.{subbing_to_id}': {
					'tier': tier.lower().strip(),
					'next_payment': datetime.now() + timedelta(days=7)
				}
			}
		},
		upsert=True
	)
