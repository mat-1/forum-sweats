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

async def set_minecraft_ign(user_id, ign, uuid):
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
	data = await member_data.find_one({
		'discord': user_id,
	})
	if data:
		return data.get('minecraft')

async def set_hypixel_rank(user_id, rank):
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
	data = await member_data.find_one({
		'discord': user_id,
	})
	if data:
		return data.get('hypixel_rank')

async def set_mute_end(user_id, end_time, extra_data={}):
	print('extra_data', extra_data)
	set_data = {
		'muted_until': end_time
	}
	for data in extra_data:
		set_data[f'muted_data.{data}'] = extra_data[data]
	await member_data.update_one(
		{
			'discord': user_id
		},
		{
			'$set': set_data
		},
		upsert=True
	)

async def get_mute_end(user_id):
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

async def add_infraction(user_id, infraction_type, reason):
	infraction_uuid = str(uuid.uuid4())
	await infractions_data.insert_one({
		'_id': infraction_uuid,
		'user': user_id,
		'type': infraction_type,
		'reason': reason,
		'date': datetime.now()
	})

async def get_infractions(user_id):
	infractions = []
	async for infraction in infractions_data.find({
		'user': user_id
	}):
		infractions.append(infraction)
	return infractions

async def clear_infractions(user_id, date):
	r = await infractions_data.delete_many({
		'user': user_id,
		'date': {
			'$gte': date,
			'$lte': date + timedelta(days=1),
		}
	})
	return r.deleted_count