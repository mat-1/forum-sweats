from typing import List
import discord
from ..gui import GUIOption, PaginationGUI, TextGUI
from ..discordbot import has_role, command_modules

name = 'help'
aliases = ['commands']
args = '[command]'

def get_data_from_module(command_module, member: discord.User):
	module_docstring: str = command_module.run.__doc__
	module_roles: List[str] = command_module.roles if hasattr(command_module, 'roles') else []
	module_name: str = command_module.name
	module_args: str = command_module.args if hasattr(command_module, 'args') else ''
	if module_roles:
		# if the user doesn't have any of the roles, dont add it
		if not any(has_role(member.id, role) for role in module_roles):
			return
	if module_docstring:
		return {
			'name': module_name,
			'args': module_args,
			'desc':module_docstring
		}


def get_help_commands(member: discord.User):
	help_commands = []

	# sort the modules by name alphabetically
	command_modules_sorted = sorted(command_modules, key=lambda m: m.name)

	for command_module in command_modules_sorted:
		data = get_data_from_module(command_module, member)
		if data:
			help_commands.append(data)
	return help_commands

def get_command_help(command_name: str, member: discord.User):
	command_name = command_name.lower()
	for command_module in command_modules:
		aliases = list(command_module.aliases if hasattr(command_module, 'aliases') else [])
		command_names = [command_module.name] + aliases
		if command_name in command_names:
			return get_data_from_module(command_module, member)


def make_text_gui(command_name: str, command_args: str, command_desc: str) -> TextGUI:
	return TextGUI(f'**{command_name}** {command_args}', command_desc)

async def run(message, command: str=None):
	'Shows an interactive GUI with all the commands this bot has.'

	help_commands = get_help_commands(message.author)

	gui_options = []

	for c in help_commands:
		command_name = c['name']
		command_args = c['args']
		command_desc = c['desc']
		gui_options.append(GUIOption(make_text_gui(command_name, command_args, command_desc), command_name))

	if command:
		c = get_command_help(command, message.author)
		if c:
			command_name = c['name']
			command_args = c['args']
			command_desc = c['desc']
			gui = make_text_gui(command_name, command_args, command_desc)
		else:
			return await message.send('That command doesn\'t exist. Do !help to see all the commands')
	else:
		gui = PaginationGUI('Commands', list(gui_options))

	await gui.make_message(message.client, message.author, message.channel)

	await gui.wait_for_option()