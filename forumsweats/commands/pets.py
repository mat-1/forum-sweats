from ..gui import PaginationGUI
from ..betterbot import Member
from typing import Dict, List
from forumsweats import db
from uuid import uuid4
import discord

name = 'pets'
channels = ['bot-commands']

PET_META: Dict[str, dict] = {
	'bobux': {
		'name': 'Bobux pet',
		'description': None
	},
	'gladiator': {
		'name': 'Gladiator pet',
		'description': None
	},
	'boulder': {
		'name': 'Boulder pet',
		'description': None
	},
	'useless': {
		'name': 'Useless pet',
		'description': 'Does absolutely nothing'
	}
}

NUMBER_EMOJIS = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')

class Pet:
	__slots__ = {'id', 'meta', 'uuid', 'provided_uuid'}

	id: str
	uuid: str
	provided_uuid: bool
	meta: dict

	def __init__(self, id: str, uuid: str=None):
		self.id = id

		# if the uuid isn't provided, set it
		if uuid:
			self.uuid = uuid
			self.provided_uuid = True
		else:
			self.uuid = uuid4().hex
			self.provided_uuid = False

		self.meta = PET_META[id]

	def to_json(self):
		return {
			'id': self.id,
			'uuid': self.uuid
		}

	def __str__(self):
		return self.meta['name']

	def __eq__(self, other):
		if hasattr(other, 'uuid'):
			return self.uuid == other.uuid
		else:
			return False

class PetsData:
	__slots__ = {'pets'}
	def __init__(self, pets: List[Pet]):
		self.pets = pets

async def get_member_pet_data_raw(member_id: int) -> List[dict]:
	# returns the pets a member has in json format
	return await db.fetch_raw_pets(member_id)

async def get_member_pet_data(member_id: int) -> PetsData:
	# returns the pets a member has as a PetsData object
	member_pet_data = await get_member_pet_data_raw(member_id)
	pets: List[Pet] = []

	# whether it found a pet without a uuid that should be updated
	should_update_pets = False

	for pet_data in member_pet_data:
		pet: Pet = Pet(**pet_data)

		# the uuid for this pet wasnt provided, we should update the pets
		if not pet.provided_uuid:
			should_update_pets = True

		pets.append(pet)

	# old pets don't have a uuid, this automatically fixes that
	if should_update_pets:
		print('Someone had a pet without a uuid, this is fixed')
		await db.set_pets(member_id, pets)

	return PetsData(pets)

async def make_pet_gui(
	pet_data: PetsData,
	pet_owner,
	user: discord.User,
) -> PaginationGUI:
	is_owner = user.id == pet_owner.id
	footer = 'React with the corresponding reaction to choose that pet. There is a 2 minute cooldown on switching pets.' if is_owner else ''
	empty_message = 'You have no pets. Do **!help pets** (TODO) to learn how to get some!' if is_owner else 'This person has no pets.'
	return PaginationGUI(
		title='Your pets' if is_owner else f'{pet_owner}\'s pets',
		options=pet_data.pets,
		footer=footer if len(pet_data.pets) >= 1 else '',
		empty=empty_message,
		selectable=is_owner
	)

async def run(message, member: Member=None):
	'Shows the pets menu. Obtaining pets is currently impossible.'

	if not member:
		member = message.author
	pet_data: PetsData = await get_member_pet_data(member.id)

	gui: PaginationGUI = await make_pet_gui(
		pet_data=pet_data,
		pet_owner=member,
		user=message.author,
	)

	pet_message: discord.Message = await gui.make_message(
		client=message.client,
		user=message.author,
		channel=message.channel,
	)

	option = await gui.wait_for_option()
	print(option, option.meta)