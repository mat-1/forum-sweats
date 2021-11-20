from ..commandparser import Member
from forumsweats import db
from ..session import s
import discord
import random
import config

name = 'connectfour'
aliases = ('connect4', 'c4',)
args = '<opponent> [opponent2] [opponent3] [opponent4] [opponent5]'

class Game:
	def __init__(self, player_count=2, width=7, height=6):
		self.width = width
		self.height = height

		# [x][y]
		# [column][row]
		self.board = [[None] * self.height for row in range(self.width)]

		# player 0 and player 1
		self.number_emojis = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')
		self.player_emojis = ['🔴', '🟡', '🔵', '🟢', '🟣', '🟤']
		self.background_emoji = '⚪'
		self.player_count = player_count
		self.turn = 0
		self.pos = ''

	def render_board(self):
		rendered = ''
		for row in range(self.height):
			for column in range(self.width):
				item = self.board[column][self.height - 1 - row]
				if item is None:
					rendered += self.background_emoji
				else:
					rendered += self.player_emojis[item]
			rendered += '\n'
		for column in range(self.width):
			rendered += self.number_emojis[column]
		return rendered

	def place(self, column, player):
		if column < 0 or column >= self.width:
			# out of bounds
			return False
		found_row = False
		row = 0
		for row in range(self.height):
			if self.board[column][row] is None:
				found_row = True
				break
		if not found_row:
			return False

		self.board[column][row] = player
		self.turn += 1
		self.turn %= self.player_count
		self.pos += str(column + 1)
		return True

	def get_position(self, position):
		column, row = position
		return self.board[column][row]

	def check_four_positions(self, a, b, c, d):
		if self.get_position(a) == self.get_position(b) == self.get_position(c) == self.get_position(d):
			return self.get_position(a)
		return None

	def check_horizontal(self):
		for row in range(self.height):
			for column in range(self.width - 3):
				check_result = self.check_four_positions(
					(column, row),
					(column + 1, row),
					(column + 2, row),
					(column + 3, row),
				)
				if check_result is not None:
					return check_result
		return None

	def check_vertical(self):
		for row in range(self.height - 3):
			for column in range(self.width):
				check_result = self.check_four_positions(
					(column, row),
					(column, row + 1),
					(column, row + 2),
					(column, row + 3),
				)
				if check_result is not None:
					return check_result
		return None

	def check_diagonal_1(self):
		# bottom left to top right
		for row in range(self.height - 3):
			for column in range(self.width - 3):
				check_result = self.check_four_positions(
					(column, row),
					(column + 1, row + 1),
					(column + 2, row + 2),
					(column + 3, row + 3),
				)
				if check_result is not None:
					return check_result
		return None

	def check_diagonal_2(self):
		# top left to bottom right
		for row in range(3, self.height):
			for column in range(self.width - 3):
				check_result = self.check_four_positions(
					(column, row),
					(column + 1, row - 1),
					(column + 2, row - 2),
					(column + 3, row - 3),
				)
				if check_result is not None:
					return check_result
		return None

	def check_winner(self):
		checks = (self.check_horizontal, self.check_vertical, self.check_diagonal_1, self.check_diagonal_2)

		for check in checks:
			check_result = check()
			if check_result is not None:
				return check_result
		return None

	def check_tie(self):
		for row in range(self.height):
			for column in range(self.width):
				item = self.board[column][row]
				if item is None:
					return False
		return True

	async def ai(self):
		async with s.get('https://connect4.gamesolver.org/solve?pos=' + self.pos) as r:
			data = await r.json()
		score = data['score']
		best_columns = []
		best_column_score = -100

		for column, value in enumerate(score):
			if None in self.board[column] and value >= best_column_score:
				if value == best_column_score:
					best_columns.append(column)
				else:
					best_columns = [column]
				best_column_score = value
		return random.choice(best_columns)



async def wait_for_number_reaction(client, message, member, emojis):
	message = await message.channel.fetch_message(message.id)
	for reaction in message.reactions:
		if reaction.count > 1:
			async for user in reaction.users():
				if not user.bot:
					await reaction.remove(user)
	while True:
		reaction, user = await client.wait_for(
			'reaction_add',
			check=(
				lambda reaction, user:
				reaction.emoji in emojis and reaction.message.id == message.id
			)
		)
		await message.remove_reaction(reaction.emoji, user)
		if user == member:
			number = emojis.index(reaction.emoji)
			if number != -1:
				return number


async def run(message, opponent: Member = None, opponent2: Member = None, opponent3: Member = None, opponent4: Member = None, opponent5: Member = None):
	'Play connect 4 with up to 5 opponents'

	if not await db.has_shop_item(message.author.id, 'connect_four'):
		return await message.send(f'You need to buy Connect Four from {config.prefix}shop.')

	if not opponent:
		return await message.channel.send('You must specify an opponent')

	embed = discord.Embed(
		title='Loading...'
	)
	game_msg = await message.send(embed=embed)

	players = [message.author, opponent]
	if opponent2: players.append(opponent2)
	if opponent3: players.append(opponent3)
	if opponent4: players.append(opponent4)
	if opponent5: players.append(opponent5)

	game = Game(len(players))

	for number in range(game.width):
		await game_msg.add_reaction(game.number_emojis[number])

	winner = None

	while winner is None:
		embed.description = game.render_board()
		turn = players[game.turn]

		embed.title = f'{turn}\'s turn'
		await game_msg.edit(embed=embed)

		if len(players) == 2 and turn.bot:
			number = await game.ai()
		else:
			number = await wait_for_number_reaction(message.client, game_msg, turn, game.number_emojis[:game.width])
		game.place(number, game.turn)

		winner = game.check_winner()
		if winner is not None:
			winner = players[winner]

		if game.check_tie():
			break

	if winner is None:
		embed.title = 'It\'s a tie'
	else:
		embed.title = f'{winner} won'
	embed.description = game.render_board()
	await game_msg.edit(embed=embed)
	await game_msg.clear_reactions()
