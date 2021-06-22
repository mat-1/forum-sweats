# TODO: make this use gui.py

import discord
import asyncio
import math
from forumsweats import db

name = 'shop'
aliases = ['bobuxshop']

PAGE_LENGTH = 10

SHOP_ITEMS = [
	# name: the item name displayed in the shop
	# price: how much bobux it costs to buy the item
	# id: the internal id for the item
	# description: the item description displayed in the shop
	# persistent: whether the item is stored in the database or not
	# activation_function (optional): the async function that is called when you buy the item, only argument is member
	{
		'name': 'Bigger rock',
		'price': 25,
		'id': 'bigger_rock',
		'description': 'Next time you throw a rock, it\'ll mute for 4 minutes rather than 1',
		'persistent': True
	},
	{
		'name': 'Tic-Tac-Toe',
		'price': 500,
		'id': 'tic_tac_toe',
		'description': 'Unlocks !tictactoe',
		'persistent': True
	}
]


backward_emoji = '◀️'
forward_emoji = '▶️'
number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']


def create_shop_embed(
	page_number,
	start_index,
	end_index,
	total_pages,
	disabled_items=set()
):
	title = 'Bobux Shop'
	description = []

	for shop_index0 in range(start_index, end_index):
		shop_index = shop_index0 + 1

		shop_item = SHOP_ITEMS[shop_index0]
		shop_item_name = shop_item['name']
		shop_item_price = shop_item['price']
		shop_item_description = shop_item['description']

		item_message = f'{shop_index % PAGE_LENGTH}) **{shop_item_name}** ({shop_item_price:,} bobux) - {shop_item_description}'
		if shop_item['id'] in disabled_items:
			item_message = f'~~{item_message}~~'

		description.append(item_message)

	embed = discord.Embed(
		title=title,
		description='\n'.join(description)
	)
	embed.set_footer(text=f'page {page_number}/{total_pages}')

	return embed


async def edit_footer_text(message, footer):
	new_embed = message.embeds[0]
	new_embed.set_footer(text=footer)
	await message.edit(embed=new_embed)


async def do_shop_gui(message, page_number=1, shop_message=None):
	bought_shop_items = await db.get_bought_shop_items(message.author.id)
	total_pages = math.ceil(len(SHOP_ITEMS) / PAGE_LENGTH)
	start_index = (page_number-1) * PAGE_LENGTH
	end_index = min((page_number) * PAGE_LENGTH, len(SHOP_ITEMS))

	disabled_items = set()
	disabled_items.update(bought_shop_items)

	embed = create_shop_embed(
		page_number=page_number,
		start_index=start_index,
		end_index=end_index,
		total_pages=total_pages,
		disabled_items=disabled_items
	)

	if shop_message:
		await shop_message.clear_reactions()
		await shop_message.edit(embed=embed)
	else:
		shop_message = await message.send(embed=embed)

	possible_reactions = []

	if page_number > 1:
		await shop_message.add_reaction(backward_emoji)
		possible_reactions.append(backward_emoji)
	for shop_index0 in range(start_index, end_index):
		number_emoji = number_emojis[shop_index0 % 10]
		shop_item = SHOP_ITEMS[shop_index0]
		if shop_item['id'] not in disabled_items:
			possible_reactions.append(number_emoji)
			await shop_message.add_reaction(number_emoji)
	if page_number < total_pages:
		await shop_message.add_reaction(forward_emoji)
		possible_reactions.append(forward_emoji)

	def reaction_check(reaction, user):
		return (
			user.id == message.author.id
			and reaction.message.id == shop_message.id
			and reaction.emoji in possible_reactions
		)

	try:
		reaction, user = await message.client.wait_for('reaction_add', timeout=120, check=reaction_check)
	except asyncio.TimeoutError:
		await shop_message.clear_reactions()
		await edit_footer_text(shop_message, 'Timed out')
		return

	if reaction.emoji == backward_emoji:
		return  # TODO: add pagination
	if reaction.emoji == forward_emoji:
		return  # TODO: add pagination
	selected_item_relative_index = number_emojis.index(reaction.emoji)
	selected_item_index = start_index + selected_item_relative_index
	selected_item = SHOP_ITEMS[selected_item_index]

	print('pog!', selected_item)
	bobux_count = await db.get_bobux(message.author.id)

	selected_item_price = selected_item['price']
	selected_item_name = selected_item['name']
	selected_item_id = selected_item['id']

	if bobux_count < selected_item_price:
		await edit_footer_text(shop_message, 'You don\'t have enough bobux to buy this')
		await shop_message.clear_reactions()
		await asyncio.sleep(5)
		return await do_shop_gui(message, page_number, shop_message)

	await db.change_bobux(message.author.id, -selected_item_price)

	await shop_message.edit(content=f'Bought **{selected_item_name}** for **{selected_item_price}** bobux', embed=None)
	await shop_message.clear_reactions()
	if selected_item['persistent']:
		await db.get_shop_item(message.author.id, selected_item_id)

	if 'activation_function' in selected_item:
		await selected_item['activation_function'](message.author)


async def run(message):
	'Lets you buy items from the Bobux shop.'
	await do_shop_gui(message)
