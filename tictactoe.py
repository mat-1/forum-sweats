import random

class Game:
	def __init__(self):
		self.board = [None for _ in range(9)]
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
		if self.board[0] == self.board[1] == self.board[2] != None: return self.board[0]
		if self.board[0] == self.board[2] == self.board[1] != None: return self.board[0]
		if self.board[1] == self.board[2] == self.board[0] != None: return self.board[0]
		# middle row
		if self.board[3] == self.board[4] == self.board[5] != None: return self.board[3]
		if self.board[3] == self.board[5] == self.board[4] != None: return self.board[3]
		if self.board[4] == self.board[5] == self.board[3] != None: return self.board[3]
		# bottom row
		if self.board[6] == self.board[7] == self.board[8] != None: return self.board[6]
		if self.board[6] == self.board[8] == self.board[7] != None: return self.board[6]
		if self.board[7] == self.board[8] == self.board[6] != None: return self.board[6]

		# left column
		if self.board[0] == self.board[3] == self.board[6] != None: return self.board[0]
		if self.board[0] == self.board[6] == self.board[3] != None: return self.board[0]
		if self.board[3] == self.board[6] == self.board[0] != None: return self.board[0]
		# middle column
		if self.board[1] == self.board[4] == self.board[7] != None: return self.board[1]
		if self.board[1] == self.board[7] == self.board[4] != None: return self.board[1]
		if self.board[4] == self.board[7] == self.board[1] != None: return self.board[1]
		# right column
		if self.board[2] == self.board[5] == self.board[8] != None: return self.board[2]
		if self.board[2] == self.board[8] == self.board[5] != None: return self.board[2]
		if self.board[5] == self.board[8] == self.board[2] != None: return self.board[2]

		# top left / bottom right
		if self.board[0] == self.board[4] == self.board[8] != None: return self.board[0]
		if self.board[0] == self.board[8] == self.board[4] != None: return self.board[0]
		if self.board[4] == self.board[8] == self.board[0] != None: return self.board[0]
		# top right / bottom left
		if self.board[2] == self.board[4] == self.board[6] != None: return self.board[2]
		if self.board[2] == self.board[6] == self.board[4] != None: return self.board[2]
		if self.board[4] == self.board[6] == self.board[2] != None: return self.board[2]

	def ai_choose(self):
		chosen = list(self._ai_get_winning_spots(self.turn))
		chosen = [position for position in list(chosen) if self.board[position] is None]
		if not chosen:
			chosen = list(self._ai_get_winning_spots('ox'[self.turn == 'o']))
		chosen = [position for position in list(chosen) if self.board[position] is None]
		if not chosen:
			if self.board[0] == self.board[2] == self.board[6] == self.board[8] == None:
				chosen = [0, 2, 6, 8]
			else:
				chosen = [position for position in range(9) if self.board[position] is None]
		return random.choice(chosen)