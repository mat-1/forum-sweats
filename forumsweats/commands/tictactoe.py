from ..commandparser import Context, Member
from forumsweats import db
import asyncio
import discord
import random
import config

name = 'tictactoe'
aliases = ['ttt']
channels = ('bot-commands', 'gulag')
args = '[opponent]'

NUMBER_EMOJIS: list = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']

class Game:
	def __init__(self):
		self.board: list = [None for _ in range(9)]
		self.turn = 'x'
		self.numbers = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']

	def place(self, position):
		if self.board[position] is None:
			self.board[position] = self.turn
		if self.turn == 'x':
			self.turn = 'o'
		else:
			self.turn = 'x'

	def render_board(self):
		rendered = ''
		for i, position in enumerate(self.board):
			if i % 3 == 0 and i > 0:
				rendered += '\n'
			if position is None:
				number = self.numbers[i]
				rendered += f':{number}:'
			elif position == 'x':
				rendered += ':x:'
			elif position == 'o':
				rendered += ':o:'
			else:
				rendered += ':question:'
		return rendered

	def _ai_get_winning_spots(self, player):
		# top row
		if self.board[0] == self.board[1] == player: yield 2
		if self.board[0] == self.board[2] == player: yield 1
		if self.board[1] == self.board[2] == player: yield 0
		# middle row
		if self.board[3] == self.board[4] == player: yield 5
		if self.board[3] == self.board[5] == player: yield 4
		if self.board[4] == self.board[5] == player: yield 3
		# bottom row
		if self.board[6] == self.board[7] == player: yield 8
		if self.board[6] == self.board[8] == player: yield 7
		if self.board[7] == self.board[8] == player: yield 6

		# left column
		if self.board[0] == self.board[3] == player: yield 6
		if self.board[0] == self.board[6] == player: yield 3
		if self.board[3] == self.board[6] == player: yield 0
		# middle column
		if self.board[1] == self.board[4] == player: yield 7
		if self.board[1] == self.board[7] == player: yield 4
		if self.board[4] == self.board[7] == player: yield 1
		# right column
		if self.board[2] == self.board[5] == player: yield 8
		if self.board[2] == self.board[8] == player: yield 5
		if self.board[5] == self.board[8] == player: yield 2

		# top left / bottom right
		if self.board[0] == self.board[4] == player: yield 8
		if self.board[0] == self.board[8] == player: yield 4
		if self.board[4] == self.board[8] == player: yield 0
		# top right / bottom left
		if self.board[2] == self.board[4] == player: yield 6
		if self.board[2] == self.board[6] == player: yield 4
		if self.board[4] == self.board[6] == player: yield 2

	def check_win(self):
		# top row
		if self.board[0] == self.board[1] == self.board[2] is not None: return self.board[0]
		if self.board[0] == self.board[2] == self.board[1] is not None: return self.board[0]
		if self.board[1] == self.board[2] == self.board[0] is not None: return self.board[0]
		# middle row
		if self.board[3] == self.board[4] == self.board[5] is not None: return self.board[3]
		if self.board[3] == self.board[5] == self.board[4] is not None: return self.board[3]
		if self.board[4] == self.board[5] == self.board[3] is not None: return self.board[3]
		# bottom row
		if self.board[6] == self.board[7] == self.board[8] is not None: return self.board[6]
		if self.board[6] == self.board[8] == self.board[7] is not None: return self.board[6]
		if self.board[7] == self.board[8] == self.board[6] is not None: return self.board[6]

		# left column
		if self.board[0] == self.board[3] == self.board[6] is not None: return self.board[0]
		if self.board[0] == self.board[6] == self.board[3] is not None: return self.board[0]
		if self.board[3] == self.board[6] == self.board[0] is not None: return self.board[0]
		# middle column
		if self.board[1] == self.board[4] == self.board[7] is not None: return self.board[1]
		if self.board[1] == self.board[7] == self.board[4] is not None: return self.board[1]
		if self.board[4] == self.board[7] == self.board[1] is not None: return self.board[1]
		# right column
		if self.board[2] == self.board[5] == self.board[8] is not None: return self.board[2]
		if self.board[2] == self.board[8] == self.board[5] is not None: return self.board[2]
		if self.board[5] == self.board[8] == self.board[2] is not None: return self.board[2]

		# top left / bottom right
		if self.board[0] == self.board[4] == self.board[8] is not None: return self.board[0]
		if self.board[0] == self.board[8] == self.board[4] is not None: return self.board[0]
		if self.board[4] == self.board[8] == self.board[0] is not None: return self.board[0]
		# top right / bottom left
		if self.board[2] == self.board[4] == self.board[6] is not None: return self.board[2]
		if self.board[2] == self.board[6] == self.board[4] is not None: return self.board[2]
		if self.board[4] == self.board[6] == self.board[2] is not None: return self.board[2]

	def ai_choose(self):
		chosen = list(self._ai_get_winning_spots(self.turn))
		chosen = [position for position in list(chosen) if self.board[position] is None]
		if not chosen:
			chosen = list(self._ai_get_winning_spots('ox'[self.turn == 'o']))
		chosen = [position for position in list(chosen) if self.board[position] is None]
		if not chosen:
			if self.board[4] is None and self.turn == 'o':
				# X--
				# -o-
				# ---
				chosen = [4]
			elif self.board[0] == self.board[2] == self.board[6] == self.board[8] is None:
				# x-x
				# ---
				# x-x
				chosen = [0, 2, 6, 8]
			elif (
				# middle is taken by the opponent
				self.board[4] and self.board[4] != self.turn
				# at least one corner is taken by the opponent
				and (self.board[0] or self.board[2] or self.board[6] or self.board[8])
				# at least one corner *isnt* taken
				and (not self.board[0] or not self.board[2] or not self.board[6] or not self.board[8])
			):
				# O-o
				# -X-
				# o-X
				if self.board[0] is None:
					chosen.append(0)
				if self.board[2] is None:
					chosen.append(2)
				if self.board[6] is None:
					chosen.append(6)
				if self.board[8] is None:
					chosen.append(8)
			elif (
				# topleft or bottomright is taken by opponent
				(self.board[0] and self.board[8]) and self.board[0] == self.board[8] != self.turn
				# topright/bottomleft is taken by opponent
				or (self.board[2] and self.board[6]) and self.board[2] == self.board[6] != self.turn
				and self.board[4] == self.turn  # middle is taken by self
				and (
					self.board[1] is None
					or self.board[3] is None
					or self.board[5] is None
					or self.board[7] is None
				)
			):
				# Xo-
				# oOo
				# -oX
				if self.board[1] is None:
					chosen.append(1)
				if self.board[3] is None:
					chosen.append(3)
				if self.board[5] is None:
					chosen.append(5)
				if self.board[7] is None:
					chosen.append(7)

		if not chosen:
			# if it's still undecided, just do random
			chosen = [position for position in range(9) if self.board[position] is None]
		return random.choice(chosen)


async def run(message, player2: Member = None):
	'Play tic-tac-toe agaisnt the bot or an opponent'

	if not await db.has_shop_item(message.author.id, 'tic_tac_toe'):
		return await message.send(f'You need to buy tic-tac-toe from {config.prefix}shop.')

	is_gulag = message.channel.id == config.channels['gulag']

	ttt_game = Game()
	player1 = message.author

	title_msg = await message.send('**TIC TAC TOE**')
	board_msg = await message.send('(loading)')

	number_emojis = list(NUMBER_EMOJIS)

	if is_gulag:
		number_emojis = list(reversed(number_emojis))
		random.shuffle(ttt_game.numbers)
		random.shuffle(number_emojis)

	for number_emoji in number_emojis:
		await board_msg.add_reaction(number_emoji)

	async def update_board():
		await board_msg.edit(content=ttt_game.render_board())
		await title_msg.edit(content=f'**TIC TAC TOE** (:{ttt_game.turn}:s turn)')

	await update_board()

	while True:
		# X
		placing_spot = 0
		if player1:
			placed = False
			while not placed:
				reaction, user = await message.client.wait_for(
					'reaction_add',
					check=(
						lambda reaction, user:
						user == player1 and reaction.emoji in number_emojis and reaction.message.id == board_msg.id
					)
				)
				placing_spot = number_emojis.index(reaction.emoji)
				placed = ttt_game.board[placing_spot] is None
		else:
			await asyncio.sleep(1)
			placing_spot = ttt_game.ai_choose()
		ttt_game.place(placing_spot)
		await update_board()
		try:
			await board_msg.clear_reaction(number_emojis[placing_spot])
		except discord.errors.Forbidden:
			await board_msg.remove_reaction(number_emojis[placing_spot], message.client.user)

		winner = ttt_game.check_win()
		if winner:
			break
		if None not in ttt_game.board:
			# tie
			break

		# O
		if player2:
			placed = False
			while not placed:
				reaction, user = await message.client.wait_for(
					'reaction_add',
					check=(
						lambda reaction, user:
						user == player2 and reaction.emoji in number_emojis and reaction.message.id == board_msg.id
					)
				)
				placing_spot = number_emojis.index(reaction.emoji)
				placed = ttt_game.board[placing_spot] is None
		else:
			await asyncio.sleep(1)
			placing_spot = ttt_game.ai_choose()
		print(placing_spot, ttt_game.turn)
		ttt_game.place(placing_spot)
		await update_board()
		try:
			await board_msg.clear_reaction(number_emojis[placing_spot])
		except discord.errors.Forbidden:
			await board_msg.remove_reaction(number_emojis[placing_spot], message.client.user)

		winner = ttt_game.check_win()
		if winner:
			break
		if None not in ttt_game.board:
			# tie
			break
	if winner:
		await title_msg.edit(content=f'**TIC TAC TOE** (:{winner}: WINS)')
	else:
		await title_msg.edit(content='**TIC TAC TOE** (it\'s a tie)')
