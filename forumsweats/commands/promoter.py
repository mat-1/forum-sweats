from forumsweats.discordbot import get_role_id
from ..commandparser import Member
from forumsweats import db
import discord
import config

name = 'promoter'
aliases = ['invites']
args = '[member]'

class HasntInvitedAnyone(Exception): pass
class UnknownInvitedMembers(Exception): pass

async def check_promoter(member, inviter_string: str=None):
	invited_member_ids = await db.get_invited_members(member.id)

	members_activity_bobux = {}

	if len(invited_member_ids) == 0:
		raise HasntInvitedAnyone()

	for member_id in invited_member_ids:
		member_object: discord.User = member.guild.get_member(member_id)
		# we do this to quickly get rid of members that arent in the server
		if member_object:
			member_activity_bobux = await db.get_activity_bobux(member_id)
			members_activity_bobux[member_id] = member_activity_bobux

	if len(members_activity_bobux) == 0:
		raise UnknownInvitedMembers()
	
	result_description = []

	total_members_invited = 0
	active_members_invited = 0

	for member_id in members_activity_bobux:
		member_activity_bobux = members_activity_bobux[member_id]
		total_members_invited += 1
		if member_activity_bobux >= 100:
			active_members_invited += 1
	

	if inviter_string:
		if total_members_invited == 1:
			if active_members_invited == 1:
				result_description = f'{inviter_string} invited 1 member total and they are active.'
			else:
				result_description = f'{inviter_string} invited 1 member total but they\'re not active.'
		else:
			result_description = f'{inviter_string} invited {total_members_invited} members total and {active_members_invited} of those members are active.'

		result_description += f' {inviter_string} need to invite 3 active members to get promoter role.'


	promoter_role_id = get_role_id(member.guild.id, 'promoter')
	promoter_role = member.guild.get_role(promoter_role_id) if promoter_role_id else None
	if not promoter_role:
		result_description = 'Error: Promoter role doesn\'t exist :('
	else:
		if active_members_invited >= 3:
			await member.add_roles(promoter_role, reason='Invited 3 active members')

	result_embed = discord.Embed(
		title='Promoter',
		description=result_description
	)

	return result_embed


async def run(message, member: Member = None):
	'Check if you can have promoter rank and give it if possible'
	if not member:
		member = message.author

	# be 100% sure the command is being run in the correct guild
	if message.guild.id != config.main_guild:
		return
	
	if member.id == message.author.id:
		inviter_string = 'You'
	else:
		inviter_string = member.mention

	result_message = await message.channel.send(embed=discord.Embed(
		title='Promoter',
		description=f'Please wait, getting activity for members {inviter_string.lower()} invited...'
	))

	try:
		embed = await check_promoter(member, inviter_string)
	except HasntInvitedAnyone:
		return await result_message.edit(content='You haven\'t invited anyone :(', embed=None)
	except UnknownInvitedMembers:
		return await result_message.edit(content='It looks like you invited someone, but they left :(', embed=None)

	await result_message.edit(content=None, embed=embed)
