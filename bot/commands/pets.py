from ..betterbot import Member
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
}

NUMBER_EMOJIS = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')

class Pet:
	__slots__ = {'id', 'meta'}
	def __init__(self, id: str):
		self.id = id
		self.meta = PET_META[id]

class PetData:
	__slots__ = {'pets'}
	def __init__(self, pets: list[Pet]):
		self.pets = pets

async def get_member_pet_data_raw(member_id: int):
	# returns the pets a member has in json format
	return {
		'pets': [
			{'id': 'bobux'},
			{'id': 'gladiator'},
			{'id': 'boulder'},
		]
	}

async def get_member_pet_data(member_id: int) -> PetData:
	# returns the pets a member has as a PetData object
	member_pet_data = await get_member_pet_data_raw(member_id)
	pets: list[Pet] = []
	for pet_data in member_pet_data['pets']:
		pet: Pet = Pet(**pet_data)
		pets.append(pet)
	return PetData(pets)

async def make_pet_gui(pet_data: PetData, pet_owner: discord.Member, is_author: bool) -> discord.Embed:
	embed_description_lines = []

	for pet_index, pet in enumerate(pet_data.pets):
		pet_name = pet.meta['name']
		pet_id = pet.id
		pet_number_emoji = NUMBER_EMOJIS[pet_index]
		embed_description_lines.append(f'{pet_number_emoji} - {pet_name}')

	embed = discord.Embed(
		title='Your pets' if is_author else f'{pet_owner}\'s pets',
		description='\n'.join(embed_description_lines)
	)
	embed.set_footer(text='React with the corresponding reaction to choose that pet. There is a 2 minute cooldown on switching pets.')
	return embed

async def run(message, member: Member=None):
	'Shows the pets menu'

	if not member:
		member = message.author
	pet_data: PetData = await get_member_pet_data(member.id)

	embed: discord.Embed = await make_pet_gui(
		pet_data,
		pet_owner=message.author,
		is_author=member.id == message.author.id
	)		

	pet_message: discord.Message = await message.channel.send(embed=embed)

	# add the number reaction for each pet
	for pet_index in range(len(pet_data.pets)):
		number_emoji: str = NUMBER_EMOJIS[pet_index]
		await pet_message.add_reaction(number_emoji)