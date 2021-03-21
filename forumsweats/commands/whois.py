from ..commandparser import Member
import discord
from forumsweats import db

name = 'whois'
args = '<member>'

async def run(message, member: Member = None):
	'Tells you the Minecraft name and UUID for a server member'
	if not member:
		return await message.send('Do `!whois @member` to get information on that user.')
	data = await db.get_minecraft_data(member.id)
	if not data:
		return await message.send(embed=discord.Embed(
			description="This user hasn't linked their account yet. Tell them to do **!link**."
		))
	embed = discord.Embed(
		title=f'Who is {member}'
	)

	uuid = data['uuid']

	embed.add_field(
		name='IGN',
		value=data['ign'],
		inline=False,
	)
	embed.add_field(
		name='UUID',
		value=uuid,
		inline=False,
	)

	embed.set_thumbnail(url=f'https://crafatar.com/renders/head/{uuid}?overlay=1')

	await message.channel.send(embed=embed)
