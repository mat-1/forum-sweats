from typing import Callable, Pattern, Union
from . import w2n
import math
import re

compiled_re_split = re.compile(r'([^\w.])')

def match_number(string: str):
	string = string.strip()
	string_split = compiled_re_split.split(string)
	for characters_remaining in range(min(len(string_split), 20), 0, -1):
		if string_split[characters_remaining - 1] == '' or string_split[characters_remaining - 1] == ' ':
			continue
		word = ''.join(string_split[:characters_remaining]).strip()
		if w2n.try_word(word):
			return word
		else:
			pass

def parse_number(string: Union[str, int]):
	# if it's not a string, just return it
	if not isinstance(string, str):
		return string
	return w2n.word_to_num(string)

TOKENS = {
	'WHITESPACE': {
		'match': re.compile(r'\s+'),
		'category': 'whitespace'
	},
	'ADD': {
		'match': re.compile(r'\+|\bplus\b'),
		'category': 'operator'
	},
	'SUB': {
		'match': re.compile(r'-|\bminus\b'),
		'category': 'operator'
	},
	'MUL': {
		'match': re.compile(r'\*|\btimes\b|×'),
		'category': 'operator'
	},
	'DIV': {
		'match': re.compile(r'\/|\bdivided by\b|÷|:'),
		'category': 'operator'
	},
	'LEFTPAREN': {
		'match': re.compile(r'\(|\bleft parenthesis\b'),
		'category': 'parenthesis'
	},
	'RIGHTPAREN': {
		'match': re.compile(r'\)|\bright parenthesis\b'),
		'category': 'parenthesis'
	},
	'POW': {
		'match': re.compile(r'\^|\*\*'),
		'category': 'operator'
	},
	'SIN': {
		'match': re.compile(r'\bsin\b'),
		'category': 'function'
	},
	'COS': {
		'match': re.compile(r'\bcos\b'),
		'category': 'function'
	},
	'TAN': {
		'match': re.compile(r'\btan\b'),
		'category': 'function'
	},

	'NUMBER': {
		# numbers and decimals
		'match': match_number,
		'category': 'number'
	},
}

OPERATOR_PRECEDENCE = {
	'POW': 3,
	'MUL': 2,
	'DIV': 2,
	'ADD': 1,
	'SUB': 1,
}

SOLVERS = {
	'ADD': lambda a, b: a + b,
	'SUB': lambda a, b: a - b,
	'MUL': lambda a, b: a * b,
	'DIV': lambda a, b: a / b,
	'SIN': lambda n: math.sin(n),
	'COS': lambda n: math.cos(n),
	'TAN': lambda n: math.tan(n),
	'POW': lambda a, b: (a ** b) if b <= 100 else 0, # we don't allow powers higher than 100 because they're too expensive
}

def is_greater_precedence(operator, other_operator):
	first_precedence = OPERATOR_PRECEDENCE[operator['name']]
	second_precedence = OPERATOR_PRECEDENCE[other_operator['name']]
	return first_precedence > second_precedence


def is_equal_precedence(operator, other_operator):
	first_precedence = OPERATOR_PRECEDENCE[operator['name']]
	second_precedence = OPERATOR_PRECEDENCE[other_operator['name']]
	return first_precedence == second_precedence


def is_function(token):
	# TODO
	print(token)
	return False

def is_left_associative(token):
	# TODO
	return True

def find_next_token(remaining_string: str):
	for token_name in TOKENS:
		token_match: Union[Pattern, Callable[[str], str]] = TOKENS[token_name]['match']
		token_category: str = TOKENS[token_name]['category']
		match_value = None

		if isinstance(token_match, Pattern):
			match_result = token_match.match(remaining_string)
			# make sure the match exists and is at the start
			if match_result and match_result.pos == 0:
				match_value = match_result[0]
		else:
			match_value = token_match(remaining_string)

		if not match_value:
			continue

		return {
			'name': token_name,
			'value': match_value,
			'category': token_category
		}

	# couldn't find anything, invalid syntax
	return None


def tokenize(string: str):
	# convert a string to an abstract array of tokens
	tokens = []
	next_token = True
	while string:
		next_token = find_next_token(string)
		if next_token is None:
			# invalid token!
			return
		tokens.append(next_token)
		string = string[len(next_token['value']):]
	return tokens

# adapted from https://en.wikipedia.org/wiki/Shunting-yard_algorithm
# changes the order of tokens to postfix to make them easier to work with
def shunting_yard_algorithm(tokens):
	output_queue = []
	operator_stack = []

	while len(tokens) > 0:
		token = tokens.pop(0)
		if token['category'] == 'number':
			output_queue.append(token)
		elif token['category'] == 'function':
			operator_stack.append(token)
		elif token['category'] == 'operator':
			while (
				(len(operator_stack) > 0)
				and (operator_stack[-1]['name'] != 'LEFTPAREN')
				and (
					(is_greater_precedence(operator_stack[-1], token))
					or (
						is_equal_precedence(operator_stack[-1], token)
						and is_left_associative(token)
					)
				)
			):
				output_queue.append(operator_stack.pop())

			operator_stack.append(token)
		elif token['name'] == 'LEFTPAREN':
			operator_stack.append(token)
		elif token['name'] == 'RIGHTPAREN':
			while operator_stack[-1]['name'] != 'LEFTPAREN':
				output_queue.append(operator_stack.pop())
			# If the stack runs out without finding a left parenthesis, then there are mismatched parentheses.
			if len(operator_stack) > 0 and operator_stack[-1]['name'] == 'LEFTPAREN':
				operator_stack.pop()
			if len(operator_stack) > 0 and operator_stack[-1]['category'] == 'function':
				output_queue.append(operator_stack.pop())

	# After while loop, if operator stack not null, pop everything to output queue
	if len(tokens) == 0:
		while len(operator_stack) > 0:
			# If the operator token on the top of the stack is a parenthesis, then there are mismatched parentheses.
			output_queue.append(operator_stack.pop())
	return output_queue

def solve_postfix(tokens):
	output_queue = []
	while len(tokens) > 0:
		token = tokens.pop(0)
		if token['category'] == 'number':
			output_queue.append(token)
		elif token['category'] == 'operator':
			# there has to be at least 2 items in the output queue, otherwise the expression is invalid
			if len(output_queue) < 2:
				return
			right_operator = output_queue.pop()['value']
			left_operator = output_queue.pop()['value']

			solver = SOLVERS[token['name']]

			try:
				result = solver(parse_number(left_operator), parse_number(right_operator))
			except ZeroDivisionError:
				# if the solver fails, return 0
				result = float('inf')

			result_token = {
				'name': 'NUMBER',
				'value': result,
				'category': 'number'
			}
			output_queue.append(result_token)
		elif token['category'] == 'function':
			# there has to be at least 1 token for functions, otherwise the expression is invalid
			if len(output_queue) < 1:
				return
			parameter = output_queue.pop()['value']
			solver = SOLVERS[token['name']]
			result = solver(parameter)
			result_token = {
				'name': 'NUMBER',
				'value': result,
				'category': 'number'
			}
			output_queue.append(result_token)

	# there's nothing in the output queue, equation is malformed
	if len(output_queue) == 0:
		return

	return parse_number(output_queue[0]['value'])

def solve_expression(string):
	# solves a mathematical expression (ex. '1+1' or '5*(1+2)-3')
	tokens = tokenize(string)
	if (tokens == None): return
	postfix_tokens = shunting_yard_algorithm(tokens)
	result = solve_postfix(postfix_tokens)
	return result

assert solve_expression('1+1') == 2
assert solve_expression('1+2*3') == 7
assert solve_expression('1+2*3-4') == 3
assert solve_expression('(1+2)*3') == 9

assert solve_expression('one + one') == 2

assert solve_expression('seven hundred and twenty seven times two million and one') == 1454000727

assert solve_expression('4 / 0') == float('inf')

assert solve_expression('( 1 * 1 * 0)') == 0

assert solve_expression('0.01') == 0.01

assert solve_expression('0.001597444089456869 * 3130') == 5

assert solve_expression('1 / 2 minus 1 / 2') == 0


