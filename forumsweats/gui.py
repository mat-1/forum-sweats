'''
Very epic Discord embed GUI utility made by mat :)
'''
from typing import Any, List, Union
import discord
import asyncio
import math


# the number emojis that can be used
NUMBER_EMOJIS = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟')
PAGE_SIZE = len(NUMBER_EMOJIS)

ARROW_LEFT = '⬅️'
ARROW_RIGHT = '➡️'

ARROW_RETURN = '↩️'

class GUI:
	'The base GUI, does nothing by default but provides utilities for other GUIs'
	client: discord.Client
	user: discord.User
	channel: discord.abc.Messageable

	title: str
	footer: str

	message: discord.Message

	reactions: List[Union[discord.Emoji, str, None]]
	ended: bool

	def __init__(
		self, title: str,
		footer: str='',
	):
		self.title = title
		self.footer = footer
		self.ended = False
	
	async def make_message(self, client: discord.Client, user: discord.User, channel: discord.abc.Messageable):
		self.client = client
		self.user = user
		self.channel = channel
		self.message = await self.channel.send('...')
		self.ended = False
		await self.from_message(self.message)
		return self.message
	
	async def from_message(self, message: discord.Message):
		self.message = message
		self.ended = False
		raise NotImplementedError()

	async def refetch_message(self):
		'Discord.py doesn\'t edit the cache when messages are reacted to, so this can be useful when checking existing reactions'
		self.message = await self.channel.fetch_message(self.message.id)
		return self.message
	

	async def set_reactions(self, expected_emojis: List[Union[discord.Emoji, str, None]]):
		'Set the reactions in the message to a list of emojis in a fast way'
		if self.ended: return
		await self.refetch_message()

		self.reactions = expected_emojis

		reactions_to_add = []
		reactions_to_remove = []

		existing_emojis: List[Union[discord.Emoji, str]] = list(map(lambda r: r.emoji, self.message.reactions))

		emojis_reconstruction: List[Union[discord.Emoji, str, None]] = list(existing_emojis)

		expected_emojis_with_filler = list(expected_emojis)


		# add filler emojis
		while len(emojis_reconstruction) > len(expected_emojis_with_filler):
			expected_emojis_with_filler.append(None)
		while len(expected_emojis_with_filler) > len(emojis_reconstruction):
			# add filler emojis
			emojis_reconstruction.append(None)

		# remove wrong emojis
		i = 0
		while i < len(emojis_reconstruction) and expected_emojis_with_filler[i] and emojis_reconstruction[i]:
			while emojis_reconstruction[i] != expected_emojis_with_filler[i] and expected_emojis_with_filler[i] and i >= 0:
				reactions_to_remove.append(emojis_reconstruction[i])
				emojis_reconstruction = emojis_reconstruction[:i] + emojis_reconstruction[i + 1:] + [None]
				i -= 1
			i += 1

		# just add all of them because why not
		for emoji in expected_emojis:
			if emoji not in emojis_reconstruction:
				reactions_to_add.append(emoji)
				emojis_reconstruction.append(emoji)

		# if it would be more efficient to just remove all the reactions, do that
		if len(reactions_to_remove) >= len(existing_emojis) / 2:
			await self.message.clear_reactions()
			reactions_to_remove = []
			reactions_to_add = expected_emojis

		# remove and add the necessary reactions
		for reaction_emoji in reactions_to_remove:
			await self.message.clear_reaction(reaction_emoji)

		for reaction_emoji in reactions_to_add:
			if reaction_emoji:
				await self.message.add_reaction(reaction_emoji)

	async def check_existing_reactions(self) -> Union[str, discord.Emoji, None]:
		'Check if there\'s a valid reaction on the message'
		if self.ended: return
		return_emoji = None

		for reaction in self.message.reactions:
			emoji = reaction.emoji
			if emoji not in self.reactions:
				asyncio.ensure_future(self.message.clear_reaction(reaction.emoji))
			elif reaction.count >= 2:
				async for reaction_user in reaction.users():
					if reaction_user.id == self.user:
						# save the emoji to return later
						return_emoji = emoji
					if not reaction_user.bot:
						# remove the reaction
						asyncio.ensure_future(self.message.remove_reaction(reaction.emoji, reaction_user))

		return return_emoji

	async def wait_for_reaction(self) -> Union[str, discord.Emoji]:
		'Returns either an Option or an arrow_left/right'
		if self.ended: return ''
		# check if there's already a valid reaction on the message, and if so return that
		existing_reaction = await self.check_existing_reactions()
		if existing_reaction:
			return existing_reaction

		def check(reaction, check_user):
			if self.user.id != check_user.id: return False
			elif reaction.emoji not in self.reactions: return False
			elif reaction.message.id != self.message.id: return False
			return True

		def check_and_delete(reaction: discord.Reaction, check_user: discord.User):
			check_result = check(reaction, check_user)
			# if the reaction is on the message and theyre not a bot, remove it
			if reaction.message.id == self.message.id and not check_user.bot:
				asyncio.ensure_future(self.message.remove_reaction(reaction.emoji, check_user))
			if check_result: return True
			return False

		reaction, user = await self.client.wait_for('reaction_add', check=check_and_delete)
	
		return reaction.emoji

	async def wait_for_end(self):
		if self.ended: return
		await self.set_reactions(self.reactions + [ARROW_RETURN])
		reaction = None
		while reaction != ARROW_RETURN:
			reaction = await self.wait_for_reaction()

	async def wait_for_option(self):
		return


class Page:
	number: int
	options: List[Any]
	title: str
	footer: str
	empty: str
	selectable: bool
	gui: GUI

	page_count: int

	def __init__(
		self, number: int, title: str, all_options: List[Any], footer: str, empty: str, selectable: bool, gui: GUI
	):
		self.number = number
		self.title = title
		self.footer = footer
		self.all_options = all_options
		self.empty = empty
		self.selectable = selectable
		self.gui = gui

		# find where the page starts and ends in relation to all the options
		page_start = self.number * PAGE_SIZE
		page_end = (self.number + 1) * PAGE_SIZE
		page_options = self.all_options[page_start:page_end]
		self.options = page_options
		self.page_count = math.ceil(len(self.all_options) / PAGE_SIZE)

	def make_embed(self) -> discord.Embed:
		page_options_numbered: List[str] = []

		option_emojis = self.get_emojis()

		for option_emoji, page_option in zip(option_emojis, self.options):
			page_options_numbered.append(f'{option_emoji} {str(page_option)}')

		embed = discord.Embed(
			title=self.title,
			description='\n'.join(page_options_numbered) or self.empty
		)

		# set the footer to page/total
		page_number_1_indexed: int = self.number + 1
		if self.page_count > 1:
			entire_footer = f'{self.footer} (Page {page_number_1_indexed}/{self.page_count})'.strip()
		else:
			# if there's only 1 page, no point in showing the page count
			entire_footer = self.footer
		embed.set_footer(text=entire_footer)

		return embed

	def get_emojis(self) -> List[Union[str, discord.Emoji, None]]:
		option_emojis: List[Union[str, discord.Emoji, None]] = []
		if self.selectable:
			for option_number in range(len(self.options)):
				option_emoji = NUMBER_EMOJIS[option_number]
				option_emojis.append(option_emoji)
		if self.number > 0:
			option_emojis.append(ARROW_LEFT)
		if self.page_count > self.number + 1:
			option_emojis.append(ARROW_RIGHT)
		return option_emojis

	async def add_reactions(self):
		expected_reactions = self.get_emojis()

		await self.gui.set_reactions(expected_reactions)

	async def edit_message_to_page(self, message: discord.Message):
		'Edit the embed and add reactions'
		embed = self.make_embed()
		await message.edit(
			content=None,  # remove the content, if it exists
			embed=embed
		)
		await self.add_reactions()


class GUIOption:
	child: GUI
	parent: GUI
	name: str

	def __init__(self, child: GUI, name: str):
		self.child = child
		self.name = name

	async def choose(self, parent: GUI):
		self.parent = parent

		# copy the attributes from the parent to the child
		self.child.client = self.parent.client
		self.child.user = self.parent.user
		self.child.channel = self.parent.channel

		await self.child.from_message(self.parent.message)

		await self.child.wait_for_end()
		await self.parent.from_message(self.parent.message)

	def __str__(self):
		return self.name


class TextGUI(GUI):
	'A GUI that just shows one page of text'
	gui: str

	def __init__(
		self,
		title: str='',
		text: str='',
		footer: str='',
	):
		self.title = title
		self.footer = footer
		self.text = text

	async def from_message(self, message: discord.Message):
		self.ended = False
		self.message = message
		embed = discord.Embed(
			title=self.title,
			description=self.text
		)
		embed.set_footer(text=self.footer)
		await message.edit(
			content=None,
			embed=embed
		)
		await self.set_reactions([])
	
	def __str__(self):
		return self.title


class PaginationGUI(GUI):
	options: List[Any]

	# the page number is 0 indexed
	page_number: int
	pages: List[Page]
	page: Page
	page_count: int

	# the message that shows up when theres no options
	empty: str
	selectable: bool

	def __init__(
		self, title: str,
		options: List[Any], empty: str='<this GUI has no items>', selectable: bool=True,
		footer: str=''
	):
		self.title = title
		self.footer = footer

		self.options = options
		self.page_count = math.ceil(len(self.options) / PAGE_SIZE) or 1
		self.empty = empty
		self.selectable = selectable

	async def from_message(self, message: discord.Message):
		self.message = message
		self.ended = False

		pages: List[Page] = []
		for page_number in range(self.page_count):
			# create the page object and add it to the pages list
			page = Page(
				gui=self,
				number=page_number,
				title=self.title,
				footer=self.footer,
				all_options=self.options,
				empty=self.empty,
				selectable=self.selectable
			)
			pages.append(page)

		self.pages = pages

		# if it has page_number then set the page to that, otherwise 0
		if hasattr(self, 'page_number'):
			await self.set_page(self.page_number)
		else:
			await self.set_page(0)


	async def set_page(self, page_number: int):
		self.page_number = page_number
		self.page = self.pages[self.page_number]

		# because of a discord.py bug, the message reactions dont update unless we do this
		await self.refetch_message()

		await self.page.edit_message_to_page(self.message)

	async def wait_for_option(self) -> Any:
		while True:
			reaction = await self.wait_for_reaction()
			if reaction == ARROW_RIGHT:
				await self.set_page(self.page_number + 1)
			elif reaction == ARROW_LEFT:
				await self.set_page(self.page_number - 1)
			else:
				# if it's not an arrow it's a number, convert it to an option
				reaction_index = NUMBER_EMOJIS.index(reaction)
				reaction_index_total = (self.page_number * PAGE_SIZE) + reaction_index

				option = self.options[reaction_index_total]

				if isinstance(option, GUIOption):
					# if it's a GUI option, then do .choose with the parent as the arg
					await option.choose(self)
				else:
					return option

	def __aiter__(self):
		return self

	async def __anext__(self):
		option = await self.wait_for_option()
		return option
		# raise StopAsyncIteration
