from .pets import PET_META, Pet
import forumsweats.discordbot as discordbot
from ..discordbot import has_role
from ..betterbot import Member
from forumsweats import db
import discord

name = 'givepet'
channels = None
roles = ('admin',)
args = '<member> <pet id>'

async def run(message, member: Member = None, pet_id: str = ''):
	'Gives a pet to a user. Don\'t abuse this!'
	if not member:
		return await message.channel.send('Invalid member')
	if pet_id not in PET_META:
		return await message.channel.send('Invalid pet id')

	pet = Pet(id=pet_id)

	await db.give_pet(member.id, pet)

	pet_name = pet.meta['name']

	await message.channel.send(
		embed=discord.Embed(
			description=f'Ok, gave a {pet_name} to <@{member.id}>.'
		)
	)
