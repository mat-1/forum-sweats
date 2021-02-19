from ..gui import PaginationGUI
from ..betterbot import Member
from forumsweats import db
import discord

name = 'pets'
channels = ['bot-commands']

PET_META: dict[str, dict] = {
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
	__slots__ = {'id', 'meta'}
	def __init__(self, id: str):
		self.id = id
		self.meta = PET_META[id]

	def to_json(self):
		return {
			'id': self.id
		}

	def __str__(self):
		return self.meta['name']

class PetsData:
	__slots__ = {'pets'}
	def __init__(self, pets: list[Pet]):
		self.pets = pets

async def get_member_pet_data_raw(member_id: int) -> list[dict]:
	# returns the pets a member has in json format
	return await db.get_pets(member_id)

async def get_member_pet_data(member_id: int) -> PetsData:
	# returns the pets a member has as a PetsData object
	member_pet_data = await get_member_pet_data_raw(member_id)
	pets: list[Pet] = []
	for pet_data in member_pet_data:
		pet: Pet = Pet(**pet_data)
		pets.append(pet)
	return PetsData(pets)

async def make_pet_gui(
	pet_data: PetsData,
	pet_owner,

	client: discord.Client,
	user: discord.User,
	channel: discord.abc.Messageable,
) -> PaginationGUI:
	is_owner = user.id == pet_owner.id
	footer = 'React with the corresponding reaction to choose that pet. There is a 2 minute cooldown on switching pets.' if is_owner else ''
	empty_message = 'You have no pets. Do **!help pets** (TODO) to learn how to get some!' if is_owner else 'This person has no pets.'
	return PaginationGUI(
		client,
		user=user,
		channel=channel,
		title='Your pets' if is_owner else f'{pet_owner}\'s pets',
		options=pet_data.pets,
		footer=footer if len(pet_data.pets) >= 1 else '',
		empty=empty_message,
		selectable=is_owner
	)

async def run(message, member: Member=None):
	'Shows the pets menu'

	if not member:
		member = message.author
	pet_data: PetsData = await get_member_pet_data(member.id)

	gui: PaginationGUI = await make_pet_gui(
		pet_data=pet_data,
		pet_owner=member,

		channel=message.channel,
		client=message.client,
		user=message.author,
	)

	pet_message: discord.Message = await gui.make_message()

	option = await gui.wait_for_option()
	print(option, option.meta)