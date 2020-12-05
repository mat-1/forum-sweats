from ..betterbot import Member
import discord

name = 'connectfour'
aliases = ['connect4', 'c4']


class Game:
	def __init__(self, player_count=2, width=7, height=6):
		self.width = width
		self.height = height

		# [x][y]
		# [column][row]
		self.board = [[None] * self.height for row in range(self.width)]

		# player 0 and player 1
		self.number_emojis = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')
		self.player_emojis = ['🔴', '🟡']
		self.background_emoji = '⚪'
		self.player_count = player_count
		self.turn = 0

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
			for column in range(self.width - 4):
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
		for row in range(self.height - 4):
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
		for row in range(self.height - 4):
			for column in range(self.width - 4):
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
			for column in range(self.width - 4):
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


async def wait_for_number_reaction(client, message, member, emojis):
	while True:
		reaction, user = await client.wait_for(
			'reaction_add',
			check=(
				lambda reaction, user:
				user == member and reaction.emoji in emojis and reaction.message.id == message.id
			)
		)
		await message.remove_reaction(reaction.emoji, user)
		number = emojis.index(reaction.emoji)
		if number != -1:
			return number


async def run(message, opponent: Member = None):
	print('connect4')
	if not opponent:
		return await message.channel.send('You must specify an opponent')

	embed = discord.Embed(
		title='Loading...'
	)
	game_msg = await message.send(embed=embed)

	players = [message.author, opponent]

	game = Game(len(players))

	for number in range(game.width):
		await game_msg.add_reaction(game.number_emojis[number])

	winner = None

	while winner is None:
		embed.description = game.render_board()
		turn = players[game.turn]

		embed.title = f'{turn}\'s turn'
		await game_msg.edit(embed=embed)

		number = await wait_for_number_reaction(message.client, game_msg, turn, game.number_emojis[:game.width])
		game.place(number, game.turn)

		winner = game.check_winner()
		if winner is not None:
			winner = players[winner]

	embed.title = f'{winner} won'
	embed.description = game.render_board()
	await game_msg.edit(embed=embed)
