from .pets import PETS_META, Pet, get_member_pet_data
from ..betterbot import Member
from forumsweats import db
from typing import Union
import discord

name = 'givepet'
channels = None
roles = ('admin',)
args = '<member> <pet id>'

async def give_pet(member_id: int, pet_id: str) -> Pet:
	pet = Pet(id=pet_id)
	await db.give_pet(member_id, pet)
	return pet

async def give_unique_pet(member: Member, pet_id: str) -> Union[Pet, None]:
	pets = await get_member_pet_data(member.id)
	for pet in pets.pets:
		# the member already has the pet, return
		if pet.id == pet_id: return
	pet = await give_pet(member.id, pet_id)
	pet_name = pet.meta['name']

	try: await member.send(f'You unlocked the **{pet_name}**')
	except: pass

	return pet

async def run(message, member: Member = None, pet_id: str = ''):
	'Gives a pet to a user. Don\'t abuse this!'
	if not member:
		return await message.channel.send('Invalid member')
	if pet_id not in PETS_META:
		return await message.channel.send('Invalid pet id')

	pet = await give_pet(member.id, pet_id)

	pet_name = pet.meta['name']

	await message.channel.send(
		embed=discord.Embed(
			description=f'Ok, gave a {pet_name} to <@{member.id}>.'
		)
	)
