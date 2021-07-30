from forumsweats.commands.pets import Pet
from typing import Any, List, Set, Union
from datetime import datetime, timedelta, timezone
import motor.motor_asyncio
import discord
import time
import uuid
import os

connection_url = os.getenv('dburi')

if not connection_url:
	print('WARNING: dburi not found in env')

client = motor.motor_asyncio.AsyncIOMotorClient(connection_url)

db = client.discord

member_data = db['members']
infractions_data = db['infractions']
servers_data = db['servers']
starboard_data = db['starboard']
giveaways_data = db['giveaways']

async def modify_member(user_id: int, data: dict):
	if not connection_url: return
	await member_data.update_one(
		{ 'discord': user_id },
		data,
		upsert=True
	)

async def set_member(user_id: int, key: str, value: Any):
	if not connection_url: return
	await modify_member(user_id, { '$set': { key: value }})

async def inc_member(user_id: int, key: str, value: int):
	if not connection_url: return
	await modify_member(user_id, { '$inc': { key: value }})

async def fetch_member(user_id: int, attribute: Union[str, None]):
	if not connection_url: return
	data = await member_data.find_one({
		'discord': int(user_id),
	})
	if data and attribute:
		return data.get(attribute)
	return data

async def set_minecraft_ign(user_id: int, ign, uuid):
	if not connection_url: return
	await set_member(
		user_id,
		'minecraft',
		{ 'ign': ign, 'uuid': uuid }
	)


async def get_minecraft_data(user_id: int):
	return await fetch_member(user_id, 'minecraft')


async def set_hypixel_rank(user_id, rank):
	await set_member(user_id, 'hypixel_rank', rank)


async def get_hypixel_rank(user_id):
	return await fetch_member(user_id, 'hypixel_rank')


async def set_mute_end(user_id, end_time, extra_data={}):
	if not connection_url: return
	set_data = {
		'muted_until': end_time
	}
	for data in extra_data:
		set_data[f'muted_data.{data}'] = extra_data[data]
	set_data['muted'] = end_time > time.time()
	return await modify_member(user_id, { '$set': set_data })


async def set_rock_immune(user_id: int, rock_immune: bool):
	await set_member(user_id, 'muted_data.rock_immune', rock_immune)


async def get_rock_immune(user_id: int) -> bool:
	'Returns whether the user is temporarily immune to rocks (because they did !gulag)'
	if not connection_url: return False
	muted_data = await fetch_member(user_id, 'muted_data') or {}
	return muted_data.get('rock_immune', False)


async def get_is_muted(user_id):
	if not connection_url: return
	data = await member_data.find_one(
		{ 'discord': int(user_id) }
	)
	if data:
		return data.get('muted', False)
	else:
		return 0


async def get_mute_end(user_id):
	if not connection_url: return 0
	data = await member_data.find_one(
		{ 'discord': int(user_id) }
	)
	if data:
		return data.get('muted_until', 0)
	else:
		return 0


async def get_mute_data(user_id) -> Any:
	if not connection_url: return {}
	data = await member_data.find_one(
		{ 'discord': int(user_id) }
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
			'muted_until': { '$gte': time.time() }
		}
	):
		active_mutes[member['discord']] = member['muted_until']
	return active_mutes


async def add_infraction(user_id: int, infraction_type, reason, mute_length=0, muted_by: int=0):
	if not connection_url: return
	infraction_uuid = str(uuid.uuid4())
	await infractions_data.insert_one({
		'_id': infraction_uuid,
		'user': user_id,
		'type': infraction_type,
		'reason': reason,
		'date': discord.utils.utcnow(),
		'length': str(mute_length),  # must be a string otherwise mongodb gets mad on long mutes
		'by': muted_by
	})


async def get_infractions(user_id: int) -> list:
	if not connection_url: return []
	infractions = []
	async for infraction in infractions_data.find({
		'user': user_id,
		'date': { '$gt': discord.utils.utcnow() - timedelta(days=30) }
	}):
		infractions.append(infraction)
	return infractions

async def get_all_infractions(user_id: int) -> list:
	if not connection_url: return []
	infractions = []
	async for infraction in infractions_data.find({
		'user': user_id,
	}):
		infractions.append(infraction)
	return infractions

async def get_all_infractions_by(user_id: int) -> list:
	if not connection_url: return []
	infractions = []
	async for infraction in infractions_data.find({
		'by': user_id,
	}):
		infractions.append(infraction)
	return infractions

async def get_weekly_warns(user_id: int) -> List[str]:
	if not connection_url: return []
	infractions = []
	async for infraction in infractions_data.find({
		'user': user_id,
		'date': { '$gt': discord.utils.utcnow() - timedelta(days=7) },
		'type': 'warn'
	}):
		infractions.append(infraction['reason'] or '<no reason>')
	return infractions


async def clear_infractions(user_id: int, date) -> int:
	if not connection_url: return 0
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
		{ 'discord': user_id },
		{
			'$set': { 'last_rock': time.time() }
		},
		upsert=True
	)


async def get_rock(user_id: int) -> int:
	if not connection_url: return 0
	data = await member_data.find_one(
		{ 'discord': int(user_id) }
	)
	if data:
		return data.get('last_rock', 0)
	else:
		return 0


async def add_message(user_id: int):
	if not connection_url: return
	hour_id = int(time.time() / 3600)
	await member_data.update_one(
		{ 'discord': user_id },
		{
			'$inc': { f'messages.{hour_id}': 1 }
		},
		upsert=True
	)


async def get_active_members_from_past_hour(hoursago=1):
	if not connection_url: return
	hour_id = int((time.time()) / 3600) - hoursago
	members = []
	async for member in member_data.find(
		{ f'messages.{hour_id}': {'$gte': 1} }
	):
		member_modified = member
		member_modified['hourly_messages'] = member['messages'].get(str(hour_id), 0)
		del member_modified['messages']
		members.append(member_modified)
	return members


async def set_is_member(user_id: int):
	if not connection_url: return
	await member_data.update_one(
		{ 'discord': user_id },
		{
			'$set': { 'member': True }
		},
		upsert=True
	)


async def get_is_member(user_id: int):
	if not connection_url: return
	data = await member_data.find_one(
		{ 'discord': int(user_id) }
	)
	if data:
		return data.get('member', False)
	else:
		return 0


async def set_counter(guild_id: int, number: int):
	if not connection_url: return
	await servers_data.update_one(
		{ 'id': guild_id },
		{
			'$set': { 'counter': number }
		},
		upsert=True
	)

async def get_counter(guild_id: int):
	if not connection_url: return 0
	data = await servers_data.find_one({
		'id': guild_id,
	})
	if data:
		return data.get('counter', 0)

async def set_infinite_counter(guild_id: int, number: int):
	if not connection_url: return
	await servers_data.update_one(
		{ 'id': guild_id },
		{
			'$set': { 'infinite_counter': number }
		},
		upsert=True
	)


async def get_infinite_counter(guild_id: int):
	if not connection_url: return 0
	data = await servers_data.find_one({
		'id': guild_id,
	})
	if data:
		return data.get('infinite_counter', 0)


async def get_last_person_in_infinite_counting(guild_id: int):
	if not connection_url: return 0
	data = await servers_data.find_one({
		'id': guild_id,
	})
	if data:
		return data.get('last_infinite_counter', 0)


async def set_last_person_in_infinite_counting(guild_id: int, member_id: int):
	if not connection_url: return
	await servers_data.update_one(
		{ 'id': guild_id },
		{
			'$set': { 'last_infinite_counter': member_id }
		},
		upsert=True
	)


async def set_last_general_duel(guild_id: int):
	if not connection_url: return
	await servers_data.update_one(
		{ 'id': guild_id },
		{
			'$set': { 'last_duel': discord.utils.utcnow() }
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
		{ 'discord': user_id },
		{
			'$set': { 'bobux': amount }
		},
		upsert=True
	)


async def get_bobux(user_id: int) -> int:
	if not connection_url: return 0
	bobux = await fetch_member(user_id, 'bobux')
	return bobux or 0

async def get_activity_bobux(user_id: int) -> int:
	if not connection_url: return 0
	bobux = await fetch_member(user_id, 'activity_bobux')
	return bobux or 0


async def change_bobux(user_id: int, amount: int, is_activity_bobux: bool=False):
	if not connection_url: return
	data_inc = { 'bobux': amount }
	if is_activity_bobux:
		data_inc['activity_bobux'] = amount
	await modify_member(user_id, 
		{ '$inc': data_inc }
	)


async def get_shop_item(user_id: int, shop_item_id: str):
	if not connection_url: return
	await member_data.update_one(
		{ 'discord': user_id },
		{
			'$set': { f'shop.{shop_item_id}': True }
		},
		upsert=True
	)


async def get_bought_shop_items(user_id: int) -> Set[Any]:
	if not connection_url: return set()
	data = await member_data.find_one(
		{ 'discord': user_id }
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
		{ 'discord': user_id },
		{
			'$set': { f'shop.{shop_item_id}': False }
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
		{ 'discord': user_id },
		{ '$set': set_data },
		upsert=True
	)


async def get_is_mooted(user_id):
	if not connection_url: return
	data = await member_data.find_one(
		{ 'discord': int(user_id) }
	)
	if data:
		return data.get('mooted', False)
	else:
		return 0


async def get_mooted_end(user_id):
	if not connection_url: return 0
	data = await member_data.find_one(
		{ 'discord': int(user_id) }
	)
	if data:
		return data.get('mooted_until', 0)
	else:
		return 0


async def get_moot_data(user_id):
	if not connection_url: return {}
	data = await member_data.find_one(
		{ 'discord': int(user_id) }
	)
	if data:
		return data.get('mooted_data', {})
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

async def get_activity_bobux_leaderboard(limit=10, page=1):
	leaderboard = []
	async for member in member_data\
		.find({'activity_bobux': {'$gte': 1}})\
		.sort('activity_bobux', -1)\
		.skip((page - 1) * limit)\
		.limit(limit):
		leaderboard.append(member)
	return leaderboard

async def get_activity_bobux_leaderboard_position(member_id: int):
	activity_bobux = await get_activity_bobux(member_id)
	position = await member_data.count_documents({'activity_bobux': {'$gte': activity_bobux}})

	return position

'''
Bobux subs
'''

async def bobux_get_subscriptions(user_id) -> list:
	if not connection_url: return []
	data = await member_data.find_one(
		{ 'discord': int(user_id) }
	)
	if data:
		subs_raw = data.get('subs', [])
	else:
		return []

	subs = []
	
	for member_id in subs_raw:
		sub_data = subs_raw[member_id]
		# convert the next payment time to be timezone-aware
		next_payment: datetime = sub_data['next_payment'].replace(tzinfo=timezone.utc)

		subs.append({
			'id': int(member_id),
			'sender': int(user_id),
			'tier': sub_data['tier'],

			'next_payment': next_payment,
			# whether the payment hasnt been given out yet (due to bot being down or something)
			'owed': discord.utils.utcnow() > next_payment
		})

	return subs


async def bobux_get_all_subscriptions(for_user=None):
	subs = []
	async for member in member_data.find(
		{ 'subs': { '$ne': None } }
	):
		subs_raw = member.get('subs', [])
		for member_id in subs_raw:
			if for_user:
				if int(for_user) != int(member_id):
					continue
			sub_data = subs_raw[member_id]

			# convert the next payment time to be timezone-aware
			next_payment: datetime = sub_data['next_payment'].replace(tzinfo=timezone.utc)

			subs.append({
				'id': int(member_id),
				'sender': int(member['discord']),
				'tier': sub_data['tier'],
				'next_payment': next_payment,
				# whether the payment hasnt been given out yet (due to bot being down or something)
				'owed': discord.utils.utcnow() > next_payment
			})
	return subs


async def bobux_subscribe_to(user_id, subbing_to_id, tier):
	if not connection_url: return
	await member_data.update_one(
		{ 'discord': user_id },
		{
			'$set': {
				f'subs.{subbing_to_id}': {
					'tier': tier.lower().strip(),
					'next_payment': discord.utils.utcnow() + timedelta(days=7)
				}
			}
		},
		upsert=True
	)


async def bobux_unsubscribe_to(user_id, unsubbing_to_id):
	if not connection_url: return
	await member_data.update_one(
		{ 'discord': user_id },
		{
			'$unset': { f'subs.{unsubbing_to_id}': '' }
		},
		upsert=True
	)

'''
Pets
'''

async def fetch_raw_pets(user_id: int) -> dict:
	member = await fetch_member(user_id, None) or {}

	return {
		'pets': member.get('pets', []),
		'active_uuid': member.get('active_pet')
	}

async def give_pet(user_id: int, pet: Pet) -> None:
	await modify_member(user_id, { '$push': { 'pets': pet.to_json() } })

async def set_pets(user_id: int, pets: List[Pet]) -> None:
	raw_pets = []
	for pet in pets:
		raw_pets.append(pet.to_json())

	await set_member(user_id, 'pets', raw_pets)

async def set_active_pet_uuid(user_id: int, pet_uuid: Union[str, None]) -> None:
	await set_member(user_id, 'active_pet', pet_uuid)




'''
Starboard
'''

cached_starboard = {}

async def add_starboard_message(message_id: int, starboard_message_id: int, star_count: int):
	cached_starboard[message_id] = {
		'message_id': message_id,
		'starboard_message_id': starboard_message_id,
		'star_count': star_count
	}
	if not connection_url: return
	await starboard_data.update_one(
		{ 'message_id': message_id },
		{
			'$set': {
				'starboard_message_id': starboard_message_id,
				'star_count': star_count
			}
		},
		upsert=True
	)

async def fetch_starboard_message(message_id: int) -> dict:
	if message_id in cached_starboard:
		return cached_starboard[message_id]
	if not connection_url: return {}
	starboard_message_data = await starboard_data.find_one({
		'message_id': message_id
	})
	return starboard_message_data or {}


'''
Invited members
'''

async def get_invited_members(user_id: int) -> List[int]:
	if not connection_url: return []
	invited_members = await fetch_member(user_id, 'invited_members')
	return invited_members or []


async def add_invited_member(user_id: int, invited_member_id: int):
	await modify_member(user_id, {
		'$addToSet': { 'invited_members': invited_member_id }
	})


'''
duel related stuff
'''

async def fetch_duel_winstreak(user_id: int) -> int:
	'Fetches the current duel winstreak for the member'
	return await fetch_member(user_id, 'duel_winstreak') or 0

async def increase_duel_winstreak(user_id: int):
	'Increase the member\'s duel winstreak by one'
	await inc_member(user_id, 'duel_winstreak', 1)

async def reset_duel_winstreak(user_id: int):
	'Reset the member\'s duel winstreak back to zero'
	await set_member(user_id, 'duel_winstreak', 0)

async def set_last_dueled_member(user_id: int, last_dueled_member_id: int):
	await set_member(user_id, 'last_dueled_member', last_dueled_member_id)

async def fetch_last_dueled_member(user_id: int) -> Union[int, None]:
	return await fetch_member(user_id, 'last_dueled_member')

'''
Giveaways
'''

async def create_new_giveaway(message_id: int, creator_id: int, channel_id: int, end: int, winners: int, bobux_requirement: int, prize: str):
	await giveaways_data.update_one(
		{ 'id': message_id },
		{
			'$set': {
				'creator_id': creator_id,
				'channel_id': channel_id,
				'end': end,
				'winners': winners,
				'bobux_requirement': bobux_requirement,
				'prize': prize,
				'ended': False
			}
		},
		upsert=True
	)
	return {
		'id': message_id,
		'creator_id': creator_id,
		'channel_id': channel_id,
		'end': end,
		'winners': winners,
		'bobux_requirement': bobux_requirement,
		'prize': prize,
		'ended': False
	}


async def get_active_giveaways():
	giveaways = []
	async for giveaway in giveaways_data.find({ 'ended': False }):
		giveaways.append(giveaway)
	return giveaways

async def get_giveaway(message_id: int):
	giveaway = await giveaways_data.find_one({ 'id': message_id })
	return giveaway

async def end_giveaway(message_id: int):
	await giveaways_data.update_one(
		{ 'id': message_id },
		{ '$set': { 'ended': True } }
	)
