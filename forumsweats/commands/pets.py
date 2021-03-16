from typing import Dict, List, TypedDict, Union
from ..gui import PaginationGUI
from ..betterbot import Member
from forumsweats import db
from uuid import uuid4
import discord

name = 'pets'
channels = ['bot-commands']

class PetMetaAbility(TypedDict):
	name: str
	description: str

class _PetMetaBase(TypedDict):
	name: str
	description: Union[str, None]

class PetMeta(_PetMetaBase, total=False):
	abilities: List[PetMetaAbility]
	emoji: str

PETS_META: Dict[str, PetMeta] = {
	'bobux': {
		'name': 'Bobux pet',
		'description': None,
		'emoji': '💰'
	},
	'gladiator': {
		'name': 'Gladiator pet',
		'description': None,
		'abilities': [
			{
				'name': 'Harder blows',
				'description': 'If you win a duel in #general, your opponent will get muted for 50% longer.'
			},
			{
				'name': 'Gladiator',
				'description': 'Adds a 10% chance to rig duels in the owner of the pet\'s favor.'
			},
		],
		'emoji': '⚔️'
	},
	'boulder': {
		'name': 'Boulder pet',
		'description': None,
		'emoji': '🪨'
	},
	'useless': {
		'name': 'Useless pet',
		'description': 'Does absolutely nothing'
	}
}

class Pet:
	__slots__ = {'id', 'meta', 'uuid', 'provided_uuid'}

	id: str
	uuid: str
	provided_uuid: bool
	meta: PetMeta

	def __init__(self, id: str, uuid: str=None):
		self.id = id

		# if the uuid isn't provided, set it
		if uuid:
			self.uuid = uuid
			self.provided_uuid = True
		else:
			self.uuid = uuid4().hex
			self.provided_uuid = False

		self.meta = PETS_META[id]

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
	__slots__ = {'pets', 'active'}

	pets: List[Pet]
	active: Union[Pet, None]

	def __init__(self, pets: List[Pet], active_uuid: str):
		self.pets = pets
		self.active = None
		for pet in pets:
			if pet.uuid == active_uuid:
				self.active = pet

async def get_member_pet_data_raw(member_id: int) -> dict:
	# returns the pets a member has in json format
	return await db.fetch_raw_pets(member_id)

async def get_member_pet_data(member_id: int) -> PetsData:
	# returns the pets a member has as a PetsData object
	member_pet_data = await get_member_pet_data_raw(member_id)
	pets: List[Pet] = []

	# whether it found a pet without a uuid that should be updated
	should_update_pets = False

	for pet_data in member_pet_data['pets']:
		pet: Pet = Pet(**pet_data)

		# the uuid for this pet wasnt provided, we should update the pets
		if not pet.provided_uuid:
			should_update_pets = True

		pets.append(pet)

	# old pets don't have a uuid, this automatically fixes that
	if should_update_pets:
		print('Someone had a pet without a uuid, this is fixed')
		await db.set_pets(member_id, pets)

	return PetsData(
		pets=pets,
		active_uuid=member_pet_data['active_uuid']
	)


async def get_active_pet(member_id: int):
	pet_data = await get_member_pet_data(member_id)
	return pet_data.active


class PetGUIOption:
	pet: Pet
	is_active: bool

	def __init__(self, pet: Pet, is_active: bool):
		self.pet = pet
		self.is_active = is_active

	def __str__(self):
		pet_name = self.pet.meta['name']
		if self.is_active:
			return f'**{pet_name}**'
		else:
			return pet_name

async def make_pet_gui(
	pet_data: PetsData,
	pet_owner,
	user: discord.User,
) -> PaginationGUI:
	is_owner = user.id == pet_owner.id

	footer = 'React with the corresponding reaction to choose that pet.' if is_owner else ''

	empty_message = 'You have no pets. Do **!help pets** to learn how to get some!' if is_owner else 'This person has no pets.'

	pet_options = []
	for pet in pet_data.pets:
		pet_options.append(PetGUIOption(
			pet,
			is_active=(pet_data.active is not None and pet.uuid == pet_data.active.uuid)
		))


	return PaginationGUI(
		title='Your pets' if is_owner else f'{pet_owner}\'s pets',
		options=pet_options,
		footer=footer if len(pet_data.pets) >= 1 else '',
		empty=empty_message,
		selectable=is_owner
	)

async def run(message, member: Member=None):
	'Shows the pets menu.\n'\
	'The current pets you can obtain are:\n'\
	'- Gladiator pet: Win 4 duels in a row against different people in #general'

	if not member:
		member = message.author

	pet_message: Union[discord.Message, None] = None
	
	while True:
		pet_data: PetsData = await get_member_pet_data(member.id)

		gui: PaginationGUI = await make_pet_gui(
			pet_data=pet_data,
			pet_owner=member,
			user=message.author,
		)

		if pet_message is not None:
			gui.client = message.client
			gui.user = message.author
			gui.channel = message.channel
			await gui.from_message(pet_message)
		else:
			pet_message = await gui.make_message(
				client=message.client,
				user=message.author,
				channel=message.channel,
			)

		option: PetGUIOption = await gui.wait_for_option()

		if not option: return

		# if the user selects the already active pet, disable it
		if pet_data.active is not None and option.pet.uuid == pet_data.active.uuid:
			await db.set_active_pet_uuid(member.id, None)
		else:
			await db.set_active_pet_uuid(member.id, option.pet.uuid)

		