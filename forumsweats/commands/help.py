from ..discordbot import has_role
import discord


name = 'help'
aliases = ['commands']


async def run(message):
	help_commands = [
		{
			'name': 'avatar',
			'args': '@member',
			'desc': 'Gets the Discord avatar for a member',
		},
		{
			'name': 'bobux',
			'args': '[@member]',
			'desc': 'Tells you how much bobux you or another member has',
		},
		{
			'name': 'bobuxleaderboard',
			'args': '',
			'desc': 'Lists the players with the most bobux',
		},
		{
			'name': 'connectfour',
			'args': '@member',
			'desc': 'Play connect four against another member',
		},
		{
			'name': 'counting',
			'args': '',
			'desc': 'Tells you the current number in #counting',
		},
		{
			'name': 'counting',
			'args': '',
			'desc': 'Tells you the current number in #counting',
		},
		{
			'name': 'duel',
			'args': '@member',
			'desc': 'Duels a member',
		},
		{
			'name': 'forum user',
			'args': '<username>',
			'desc': 'Gets the forum stats for a username',
		},
		{
			'name': 'gulag',
			'args': '[time]',
			'desc': 'Puts you in gulag for one minute',
		},
		{
			'name': 'infractions',
			'args': '',
			'desc': 'Tells you your infractions',
		},
		{
			'name': 'infractions',
			'args': '',
			'desc': 'Tells you your infractions',
		},
		{
			'name': 'link',
			'args': '<ign>',
			'desc': 'Links your Discord account to your Minecraft account and gives you Hypixel rank roles',
		},
		{
			'name': 'e',
			'args': '',
			'desc': 'e',
		},
		{
			'name': 'rock',
			'args': '@member',
			'desc': "Extends the length of a user's time in gulag by 5 minutes",
		},
		{
			'name': 'tictactoe',
			'args': '[@member]',
			'desc': 'Lets you play tic-tac-toe against another member or against AI',
		},
		{
			'name': 'shitpost',
			'args': '',
			'desc': 'Generates a shitpost using a markov chain',
		},
	]

	if has_role(message.author.id, 'helper'):
		help_commands.extend([
			{
				'name': 'mute',
				'args': '@member <length> [reason]',
				'desc': 'Mutes a user from sending messages for a certain amount of time',
			},
			{
				'name': 'unmute',
				'args': '@member',
				'desc': 'Unmutes a user early so they can send messages',
			},
			{
				'name': 'infractions',
				'args': '@member',
				'desc': 'View the infractions of another member (mutes, warns, etc)',
			},
			{
				'name': 'clearinfractions',
				'args': '@member <mm/dd/yyyy>',
				'desc': 'Clear the infractions for a member from a specific date',
			}
		])
	else:
		help_commands.extend([
			{
				'name': 'infractions',
				'args': '',
				'desc': 'View your own infractions (mutes, warns, etc)',
			}
		])

	description = []

	for command in help_commands:
		command_name = command['name']
		command_args = command['args']
		command_desc = command['desc']
		if command_args:
			command_title = f'!**{command_name}** {command_args}'
		else:
			command_title = f'!**{command_name}**'
		description.append(
			f'{command_title} - {command_desc}'
		)

	embed = discord.Embed(title='Commands', description='\n'.join(description))
	await message.send(embed=embed)
