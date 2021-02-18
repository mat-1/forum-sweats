from typing import Iterator, Union
import discord
import math


# the number emojis that can be used
NUMBER_EMOJIS = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')
PAGE_SIZE = len(NUMBER_EMOJIS)

ARROW_LEFT = '⬅️'
ARROW_RIGHT = '➡️'

class Page:
	number: int
	options: list[str]
	title: str

	page_count: int

	def __init__(self, number: int, title: str, all_options: list[str]):
		self.number = number
		self.title = title
		self.all_options = all_options

		# find where the page starts and ends in relation to all the options
		page_start = self.number * PAGE_SIZE
		page_end = (self.number + 1) * PAGE_SIZE
		page_options = self.all_options[page_start:page_end]
		self.options = page_options

		self.page_count = math.ceil(len(self.all_options) / PAGE_SIZE)

	def make_embed(self) -> discord.Embed:
		page_options_numbered: list[str] = []

		option_emojis = self.get_emojis()

		for option_emoji, page_option in zip(option_emojis, self.options):
			page_options_numbered.append(f'{option_emoji} {page_option}')

		embed = discord.Embed(
			title=self.title,
			description='\n'.join(page_options_numbered)
		)

		# set the footer to page/total
		page_number_1_indexed: int = self.number + 1
		embed.set_footer(text=f'(Page {page_number_1_indexed}/{self.page_count})')

		return embed

	def get_emojis(self) -> list[str]:
		option_emojis: list[str] = []
		for option_number in range(len(self.options)):
			option_emoji = NUMBER_EMOJIS[option_number]
			option_emojis.append(option_emoji)
		return option_emojis

	async def add_reactions(self, message: discord.Message):
		existing_reactions = message.reactions
		existing_reaction_numbers = []

		left_arrow_expected = self.number > 0
		right_arrow_expected = self.page_count > self.number + 1

		print('right_arrow_expected', right_arrow_expected, self.page_count, self.number)


		left_arrow_found = False
		right_arrow_found = False

		for existing_reaction in existing_reactions:
			emoji = str(existing_reaction.emoji)
			if emoji in NUMBER_EMOJIS:
				emoji_number = NUMBER_EMOJIS.index(emoji)
				existing_reaction_numbers.append(emoji_number)
			else:
				if emoji == ARROW_LEFT:
					left_arrow_found = True
				if emoji == ARROW_RIGHT:
					right_arrow_found = True

		expected_reaction_numbers = list(range(len(self.options)))

		reactions_to_add = []
		reactions_to_remove = []

		# if there's expected numbers that aren't there, add them to reactions_to_add
		for expected_number in expected_reaction_numbers:
			if expected_number not in existing_reaction_numbers:
				reactions_to_add.append(NUMBER_EMOJIS[expected_number])

		# if there's unexpected numbers that are there, add them to reactions_to_remove
		for existing_number in existing_reaction_numbers:
			if existing_number not in expected_reaction_numbers:
				reactions_to_remove.append(NUMBER_EMOJIS[existing_number])


		# remove left arrow
		if left_arrow_found and not left_arrow_expected:
			reactions_to_remove.append(ARROW_LEFT)
		# remove right arrow
		if right_arrow_found and not right_arrow_expected:
			reactions_to_remove.append(ARROW_RIGHT)
		
		# add left arrow
		if left_arrow_expected and not left_arrow_found:
			# we need to remove and readd the right arrow so its in the correct order
			if right_arrow_expected: reactions_to_remove.append(ARROW_RIGHT)
			reactions_to_add.append(ARROW_LEFT)
			if right_arrow_expected: reactions_to_add.append(ARROW_RIGHT)
		
		if left_arrow_found and left_arrow_expected and ARROW_LEFT not in reactions_to_add and len(reactions_to_add) >= 1:
			# remove and readd the left arrow to make sure its at the end
			reactions_to_remove.append(ARROW_LEFT)
			reactions_to_add.append(ARROW_LEFT)

		if right_arrow_found and right_arrow_expected and ARROW_RIGHT not in reactions_to_add and len(reactions_to_add) >= 1:
			# remove and readd the right arrow to make sure its at the end
			reactions_to_remove.append(ARROW_RIGHT)
			reactions_to_add.append(ARROW_RIGHT)

		# add right arrow
		if right_arrow_expected and not right_arrow_found:
			reactions_to_add.append(ARROW_RIGHT)


		# remove and add the necessary reactions
		for reaction_emoji in reactions_to_remove:
			await message.clear_reaction(reaction_emoji)

		for reaction_emoji in reactions_to_add:
			await message.add_reaction(reaction_emoji)

	async def edit_message_to_page(self, message: discord.Message):
		'Edit the embed and add reactions'
		embed = self.make_embed()
		await message.edit(
			content=None,  # remove the content, if it exists
			embed=embed
		)
		await self.add_reactions(message)

	async def wait_for_reaction(self, client: discord.Client, message: discord.Message, user: discord.User) -> str:
		'Returns either an Option or an arrow_left/right'
		valid_reactions = self.get_emojis()


		left_arrow_expected = self.number > 0
		right_arrow_expected = self.page_count > self.number + 1

		if left_arrow_expected: valid_reactions.append(ARROW_LEFT)
		if right_arrow_expected: valid_reactions.append(ARROW_RIGHT)

		def check(reaction, check_user):
			if user.id != check_user.id: return False
			elif reaction.emoji not in valid_reactions: return False
			elif reaction.message.id != message.id: return False
			return True

		reaction, user = await client.wait_for('reaction_add', check=check)

		if reaction.emoji == ARROW_LEFT: return ARROW_LEFT
		elif reaction.emoji == ARROW_RIGHT: return ARROW_RIGHT

		reaction_index = valid_reactions.index(reaction.emoji)
		reaction_index_total = (self.number * PAGE_SIZE) + reaction_index
		print(reaction_index_total)
		return self.all_options[reaction_index_total]


class GUI:
	client: discord.Client
	user: discord.User
	channel: discord.abc.Messageable

	title: str

	message: discord.Message

	def __init__(self, client: discord.Client, user: discord.User, channel: discord.abc.Messageable, title: str):
		self.client = client
		self.user = user
		self.channel = channel

		self.title = title
	
	async def make_message(self):
		raise NotImplementedError()

	async def refetch_message(self):
		self.message = await self.message.channel.fetch_message(self.message.id)

class PaginationGUI(GUI):
	options: list[str]

	# this is 0 indexed!
	page_number: int
	pages: list[Page]
	page: Page

	def __init__(
		self, client: discord.Client, user: discord.User, channel: discord.abc.Messageable, title: str,
		options: list[str],
	):
		self.client = client
		self.user = user
		self.channel = channel

		self.title = title
		self.options = options

		self.page_count = math.ceil(len(self.options) / PAGE_SIZE)

	async def make_message(self) -> discord.Message:
		'Make an embed GUI where the user can choose an option. Multiple pages are automatically created.'

		self.message = await self.channel.send('...')

		pages: list[Page] = []
		for page_number in range(self.page_count):
			# create the page object and add it to the pages list
			page = Page(
				number=page_number,
				title=self.title,
				all_options=self.options
			)
			pages.append(page)

		self.pages = pages

		await self.set_page(0)

		return self.message

		# gui_open = True

		# while gui_open:
		# 	page: Page = pages[page_number]
		# 	await page.edit_message_to_page(message)
		# 	option = await page.wait_for_reaction(client, message, user)
		# 	yield option

		# 	if not forever:
		# 		# if the gui isn't going to be open forever, close it now
		# 		gui_open = False

	async def set_page(self, page_number: int):
		self.page_number = page_number
		print('setting page to', page_number)
		self.page = self.pages[self.page_number]

		# because of a discord.py bug, the message reactions dont update unless we do this
		await self.refetch_message()

		await self.page.edit_message_to_page(self.message)

	async def wait_for_reaction(self) -> str:
		reaction = await self.page.wait_for_reaction(self.client, self.message, self.user)
		return reaction

	async def wait_for_and_process_reaction(self) -> str:
		while True:
			reaction = await self.wait_for_reaction()
			if reaction == ARROW_RIGHT:
				await self.set_page(self.page_number + 1)
			elif reaction == ARROW_LEFT:
				await self.set_page(self.page_number - 1)
			else:
				# number
				return reaction

	async def wait_for_option(self) -> str:
		return await self.wait_for_and_process_reaction()

	def __aiter__(self):
		return self

	async def __anext__(self):
		option = await self.wait_for_option()
		return option
		# raise StopAsyncIteration
