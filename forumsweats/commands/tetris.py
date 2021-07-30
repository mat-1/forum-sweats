import asyncio
import config
from forumsweats import db
import time
from typing import Any, Dict, List, Literal, Union
from forumsweats.commandparser import Context
import discord
import random

name = 'tetris'
aliases = ['tetris']

pieces = [
	{
		# I piece
		'color': '🟦',
		'shape': [
			[1, 1, 1, 1]
		]
	},
	{
		# J piece
		'color': '🟫',
		'shape': [
			[1, 0, 0],
			[1, 1, 1]
		]
	},
	{
		# L piece
		'color': '🟧',
		'shape': [
			[0, 0, 1],
			[1, 1, 1]
		]
	},
	{
		# O piece
		'color': '🟨',
		'shape': [
			[1, 1],
			[1, 1]
		]
	},
	{
		# S piece
		'color': '🟩',
		'shape': [
			[0, 1, 1],
			[1, 1, 0]
		]
	},
	{
		# T piece
		'color': '🟪',
		'shape': [
			[0, 1, 0],
			[1, 1, 1]
		]
	},
	{
		# Z piece
		'color': '🟥',
		'shape': [
			[1, 1, 0],
			[0, 1, 1]
		]
	}
]

background_color = '⬛'

board_width = 10
# board_height = 20
board_height = 19 # discord limits the number of emojis a message can have to 199

default_board = [
	[ background_color ] * board_height
] * board_width

def is_position_possible(game_board, shape: List[List[Literal[0, 1]]], x: int, y: int):
	'Check if the piece can be at a given position'

	for relative_y, row in enumerate(shape):
		for relative_x, cell in enumerate(row):
			if cell:
				if x + relative_x < 0 or x + relative_x >= board_width:
					return False
				if y + relative_y < 0 or y + relative_y >= board_height:
					return False
				if game_board[x + relative_x][y + relative_y] != background_color:
					return False
	return True

def render_board_embed(original_game_board, score: int, held_piece=None, piece=None, piece_x: int=None, piece_y: int=None):
	'Create an embed for the Tetris board'
	# copy the board so we don't modify the original
	game_board = [ row[:] for row in original_game_board ]

	if piece and piece_x is not None and piece_y is not None:
		# overlay the piece onto the game board
		game_board = overlay_piece_onto_board(game_board, piece, piece_x, piece_y)
		# overlay the ghost, which is always at the place where the piece would be if it drops
		ghost_piece = { 'color': '⚫', 'shape': piece['shape'] }
		ghost_piece_y = piece_y
		while is_position_possible(original_game_board, ghost_piece['shape'], piece_x, ghost_piece_y + 1):
			ghost_piece_y += 1
		game_board = overlay_piece_onto_board(game_board, ghost_piece, piece_x, ghost_piece_y)


	board_render = ''
	for y in range(len(game_board[0])):
		for x in range(len(game_board)):
			board_render += game_board[x][y]
		board_render += f'\n'
	embed = discord.Embed(
		title = f'Tetris (score: {score:,})',
		description = board_render,
		colour = discord.Colour.blue(),
	)
	if held_piece:
		held_piece_render = ''
		for x in range(len(held_piece['shape'])):
			for y in range(len(held_piece['shape'][0])):
				held_piece_render += held_piece['color'] if held_piece['shape'][x][y] else background_color
			held_piece_render += '\n'
		embed.add_field(
			name = 'Holding Piece',
			value = held_piece_render
		)
	return embed

def overlay_piece_onto_board(game_board, piece, piece_x, piece_y):
	'Overlay the piece onto the board'
	for y, row in enumerate(piece['shape']):
		for x, cell in enumerate(row):
			if cell and game_board[piece_x + x][piece_y + y] == background_color:
				game_board[piece_x + x][piece_y + y] = piece['color']
	return game_board

def rotate_shape_clockwise(shape):
	'Rotate the shape clockwise'
	return [ [ shape[y][x] for y in range(len(shape)-1, -1, -1) ] for x in range(len(shape[0])) ]

def rotate_shape_counterclockwise(shape):
	'Rotate the shape counterclockwise'
	return [ [ shape[y][x] for y in range(len(shape)) ] for x in range(len(shape[0])-1, -1, -1) ]

async def run(message: Context):
	'Play Tetris in Discord'

	if not await db.has_shop_item(message.author.id, 'tetris'):
		return await message.send(f'You need to buy tetris from {config.prefix}shop.')

	# the game board, this doesn't include the current piece that is moving
	game_board = [ row[:] for row in default_board ]

	view = discord.ui.View(timeout=None)
	ui_button_left = discord.ui.Button(
		custom_id='left',
		style=discord.ButtonStyle.primary,
		emoji='◀️',
		row=1
	)
	view.add_item(ui_button_left)

	ui_button_drop = discord.ui.Button(
		custom_id='drop',
		style=discord.ButtonStyle.success,
		emoji='⏬',
		row=1
	)
	view.add_item(ui_button_drop)

	ui_button_right = discord.ui.Button(
		custom_id='right',
		style=discord.ButtonStyle.primary,
		emoji='▶️',
		row=1
	)
	view.add_item(ui_button_right)

	ui_button_spin_counterclockwise = discord.ui.Button(
		custom_id='spin_counterclockwise',
		style=discord.ButtonStyle.secondary,
		emoji='🔄',
		row=2
	)
	view.add_item(ui_button_spin_counterclockwise)

	ui_button_down = discord.ui.Button(
		custom_id='down',
		style=discord.ButtonStyle.primary,
		emoji='🔽',
		row=2
	)
	view.add_item(ui_button_down)

	ui_button_spin_clockwise = discord.ui.Button(
		custom_id='spin_clockwise',
		style=discord.ButtonStyle.secondary,
		emoji='🔃',
		row=2
	)
	view.add_item(ui_button_spin_clockwise)


	ui_button_hold = discord.ui.Button(
		custom_id='hold',
		style=discord.ButtonStyle.secondary,
		emoji='♻️',
		row=3
	)
	view.add_item(ui_button_hold)


	game_message = await message.reply(
		embed = render_board_embed(game_board, 0),
		view = view
	)
	

	# whether the game hasn't ended
	playing = True
	# the current piece
	piece: Union[dict[str, Any], None] = None
	piece_x = 0
	piece_y = 0

	held_piece = None

	last_edit = time.time()

	bag = []

	score = 0

	def choose_piece():
		'Choose a random piece to play'
		nonlocal bag

		# https://tetris.fandom.com/wiki/Random_Generator
		if not bag:
			bag = [ piece for piece in pieces ]
			random.shuffle(bag)

		return bag.pop()
	
	def choose_new_piece(new_piece: Dict[str, Any]=None):
		'Choose a new piece to place'
		nonlocal piece
		nonlocal piece_x
		nonlocal piece_y

		piece = new_piece or choose_piece()
		piece_x = int(board_width / 2 - len(piece['shape'][0]) / 2)
		piece_y = 0


	async def on_interact(interaction: discord.interactions.Interaction):
		# this prevents other people from interacting with the game
		return interaction.user == message.author

	async def button_click_left(interaction: discord.interactions.Interaction):
		nonlocal piece_x
		nonlocal piece_y
		nonlocal piece
		if piece and is_position_possible(game_board, piece['shape'], piece_x - 1, piece_y):
			piece_x -= 1
	
	async def button_click_right(interaction: discord.interactions.Interaction):
		nonlocal piece_x
		nonlocal piece_y
		nonlocal piece
		if piece and is_position_possible(game_board, piece['shape'], piece_x + 1, piece_y):
			piece_x += 1
	
	async def button_click_spin_clockwise(interaction: discord.interactions.Interaction):
		nonlocal piece_x
		nonlocal piece_y
		nonlocal piece
		if not piece: return
		new_shape = rotate_shape_clockwise(piece['shape'])
		if is_position_possible(game_board, new_shape, piece_x, piece_y):
			piece['shape'] = new_shape

	async def button_click_spin_counterclockwise(interaction: discord.interactions.Interaction):
		nonlocal piece_x
		nonlocal piece_y
		nonlocal piece
		if not piece: return
		new_shape = rotate_shape_counterclockwise(piece['shape'])
		if is_position_possible(game_board, new_shape, piece_x, piece_y):
			piece['shape'] = new_shape
	
	async def button_click_down(interaction: discord.interactions.Interaction):
		nonlocal piece_x
		nonlocal piece_y
		nonlocal piece
		nonlocal score

		if piece and is_position_possible(game_board, piece['shape'], piece_x, piece_y + 1):
			piece_y += 1
			score += 1
	
	async def button_click_drop(interaction: discord.interactions.Interaction):
		nonlocal piece_x
		nonlocal piece_y
		nonlocal piece
		nonlocal score

		while piece and is_position_possible(game_board, piece['shape'], piece_x, piece_y + 1):
			piece_y += 1
			score += 2
	
	async def button_click_hold(interaction: discord.interactions.Interaction):
		nonlocal piece_x
		nonlocal piece_y
		nonlocal piece
		nonlocal held_piece
		if held_piece is None:
			held_piece = piece
			choose_new_piece()
		else:
			piece, held_piece = held_piece, piece
			choose_new_piece(piece)

	def clear_lines():
		'Clear any full lines and award points'
		nonlocal game_board
		nonlocal score
		nonlocal bag

		lines_cleared = 0

		y = board_height - 1
		while y > 0:
			if all(row[y] != background_color for row in game_board):
				# remove the column
				for x in range(board_width):
					game_board[x].pop(y)
				# shift everything down
				for x in range(board_width):
					game_board[x].insert(0, background_color)
				lines_cleared += 1
			else:
				y -= 1
		if lines_cleared == 1:
			score += 100
		elif lines_cleared == 2:
			score += 300
		elif lines_cleared == 3:
			score += 500
		elif lines_cleared == 4:
			score += 800


	view.interaction_check = on_interact
	ui_button_left.callback = button_click_left
	ui_button_right.callback = button_click_right
	ui_button_spin_clockwise.callback = button_click_spin_clockwise
	ui_button_spin_counterclockwise.callback = button_click_spin_counterclockwise
	ui_button_down.callback = button_click_down
	ui_button_drop.callback = button_click_drop
	ui_button_hold.callback = button_click_hold

	choose_new_piece()

	while playing:
		# do the game loop
		last_edit = time.time()
		if piece:
			await game_message.edit(
				embed = render_board_embed(game_board, score, held_piece, piece, piece_x, piece_y)
			)
		else:
			await game_message.edit(
				embed = render_board_embed(game_board, score, held_piece)
			)
			choose_new_piece()
			if piece and not is_position_possible(game_board, piece['shape'], piece_x, piece_y):
				playing = False

		await asyncio.sleep(time.time() - last_edit + 1)
		
		if piece and is_position_possible(game_board, piece['shape'], piece_x, piece_y + 1):
			piece_y += 1
		else:
			# the piece can't be moved down anymore, choose a new piece
			game_board = overlay_piece_onto_board(game_board, piece, piece_x, piece_y)
			piece = None
			clear_lines()

	embed = render_board_embed(game_board, score, held_piece)
	embed.title = f'Game over (score: {score:,})'
	await game_message.edit(embed = embed)
	view.stop()
