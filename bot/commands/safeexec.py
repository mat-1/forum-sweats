from dis import dis
from types import FunctionType
import functools
import asyncio
import discord
import traceback

name = 'safeexec'
aliases = ['safeeval', 'execsafe', 'evalsafe']


class ReachedMaxSteps(Exception): pass


class Interpreter():
	async def POP_TOP(self, value=None):  # 1
		print('pop top', self.data_stack)
		return self.data_stack.pop()

	async def RETURN_VALUE(self, _):  # 83
		if len(self.call_stack) == 0 or self.is_function:
			TOS = await self.POP_TOP()
			self.returned = TOS
			self.done = True

	async def BINARY_MATH(self, bin_op):
		val1 = await self.POP_TOP()
		val2 = await self.POP_TOP()
		out = self.bin_ops[bin_op](val1, val2)
		self.data_stack.append(out)
		return out

	async def BINARY_MODULO(self, _):  # 22
		return self.BINARY_ADD('%')

	async def BINARY_ADD(self, _):  # 23
		return self.BINARY_MATH('+')

	async def BINARY_FLOOR_DIVIDE(self, _):
		return self.BINARY_MATH('//')

	async def POP_BLOCK(self, _):
		block = self.block_stack.pop()
		bytecode_target = block[1] + block[2]
		# self.bytecode_counter = bytecode_target
		return block

	async def STORE_NAME(self, namei):  # 90
		name = self.co_names[namei]
		TOS = await self.POP_TOP()
		self.variables[name] = TOS

	async def BUILD_TUPLE(self, count):
		output_list = []
		for _ in range(count):
			output_list.insert(0, await self.POP_TOP())
		out = (*output_list,)
		self.data_stack.append(out)

	async def BUILD_LIST(self, count):
		output = []
		for _ in range(count):
			output.insert(0, await self.POP_TOP())
		self.data_stack.append(output)
		return output

	async def LOAD_CONST(self, value):  # 100
		print('LOAD_CONST')
		const_value = self.co_consts[value]
		self.data_stack.append(const_value)

	async def LOAD_NAME(self, value):  # 101
		name_value = self.co_names[value]
		if name_value in self.variables:
			variable = self.variables[name_value]
		elif name_value in self.global_variables:
			variable = self.global_variables[name_value]
		else:
			raise NameError()
		self.data_stack.append(variable)

	async def UNPACK_SEQUENCE(self, count):
		individial_values = []
		TOS = await self.POP_TOP()
		for i in range(count):
			individial_values.insert(0, TOS[i])
		if len(TOS) > count:
			individial_values.append(TOS[count:])
		for i in individial_values:
			self.data_stack.append(i)

	async def COMPARE_OP(self, opname):  # 107
		op = self.cmp_op[opname]
		val1 = await self.POP_TOP()
		val2 = await self.POP_TOP()
		out = op(val1, val2)

		self.data_stack.append(out)

	async def IMPORT_NAME(self, namei):
		# nope :)
		return
		module_name = self.co_names[namei]
		fromlist = await self.POP_TOP()
		level = await self.POP_TOP()
		the_module = __import__(module_name, fromlist=fromlist, level=level)
		self.data_stack.append(the_module)

	async def JUMP_FORWARD(self, delta):
		self.bytecode_counter += delta // 2

	async def JUMP_ABSOLUTE(self, target):
		self.bytecode_counter = target // 2

	async def POP_JUMP_IF_FALSE(self, target):  # 114
		TOS = await self.POP_TOP()
		if TOS is False:
			self.bytecode_counter = target // 2

	async def LOAD_GLOBAL(self, namei):  # 116
		name_value = self.co_names[namei]
		variable = self.global_variables[name_value]
		self.data_stack.append(variable)

	async def add_to_block_stack(self, block_type, delta):
		self.block_stack.append((
			block_type,
			self.bytecode_counter,
			delta // 2
		))

	async def SETUP_LOOP(self, delta):  # 120
		self.add_to_block_stack('loop', delta)

	async def SETUP_EXCEPT(self, delta):  # 121
		self.add_to_block_stack('except', delta)

	async def GET_ITER(self, _):
		TOS = await self.POP_TOP()
		TOS = iter(TOS)
		self.data_stack.append(TOS)

	async def FOR_ITER(self, delta):
		TOS = self.data_stack[-1]
		try:
			next_value = TOS.__next__()
		except StopIteration:
			self.bytecode_counter += delta // 2
		else:
			self.data_stack.append(next_value)

	async def LOAD_BUILD_CLASS(self, _):
		# this is trash
		# def build_class_wrapper(func, *args, **kw):
		# 	# if its a Interpreter.execute
		# 	if (func.__name__ == "execute" and
		# 		hasattr(func, "__self__") and
		# 		isinstance(func.__self__, Interpreter)):
		# 		interp = func.__self__
		# 		def func():
		# 			interp.variables.update(locals())
		# 			return interp.execute()

		# 	return __build_class__(func, *args, **kw)
		def build_class_wrapper(func, *args, **kwargs):
			if hasattr(func, '__self__') and isinstance(func.__self__, Interpreter):
				# func = lambda *args:func.__self__.execute(*args)
				func = functools.partial(func, *args, **kwargs)
			else:
				return __build_class__(func, *args, **kwargs)
		self.data_stack.append(build_class_wrapper)

	async def LOAD_FAST(self, var_num):
		name_value = self.co_varnames[var_num]
		variable = self.references[var_num]
		self.data_stack.append(variable)
		return variable

	async def STORE_FAST(self, var_num):  # 125
		TOS = await self.POP_TOP()
		self.references = list(self.references)
		if var_num >= len(self.references):
			self.references.append(TOS)
		else:
			self.references[var_num] = TOS

	async def CALL_FUNCTION(self, value):  # 131
		function_args = []
		for _ in range(value):
			arg = await self.POP_TOP()
			function_args.insert(0, arg)

		function = await self.POP_TOP()

		if asyncio.iscoroutinefunction(function):
			function_return = await function(*function_args)
		else:
			function_return = function(*function_args)

		self.data_stack.append(function_return)

	async def MAKE_FUNCTION(self, argc):
		func_name = await self.POP_TOP()
		func_code = await self.POP_TOP()
		i = Interpreter(func_code, name=func_name)
		i.global_variables = self.global_variables
		func_exec = i.execute
		self.data_stack.append(func_exec)
		return func_exec

	async def LOAD_METHOD(self, namei):
		"""
		if there's a custom getattr or name is non-string: getattr, do the null thing
		if the type isn't loaded somehow (??): break it

		get an attribute from the class (how to do without C api, ctypes? ugly though)
		if its a method: do the good thing
		else: do the null thing

		try getting it from the dict, then do the null thing
		"""
		# TODO: make this not horrible and pasta-like
		# also how to represent NULL on stack? None
		# is there any situation where there isnt a CALL_METHOD directly after?

		# ACTUALLY
		# it might be *less* hacky to just throw together a function that uses the builtin LOAD_METHOD
		# with bytecode
		# passing the name is hard though
		# ctypes maybe?
		# can co_names be a list instead of tuple so we can mutate it?

		# all that is stupid, for now just do the dumb way thats probably 10x faster
		method_name = self.co_names[namei]
		TOS = await self.POP_TOP()

		self.data_stack.append(None)
		self.data_stack.append(getattr(TOS, method_name))
		return

		# slow but spec-following way:
		def get_from_type(type_, attr):
			"""get an attribute from a type or a parent in its mro"""
			# does this even work this feels sketchy
			for parent in type_.mro():
				if method_name in parent.__dict__:
					return parent.__dict__[method_name]
			raise AttributeError()
		if type(TOS).__getattribute__ != object.__getattribute__:
			# if there's a custom getattr or name is non-string: getattr, do the null thing
			self.data_stack.append(None)
			self.data_stack.append(getattr(TOS, method_name))
			return

		try:
			# get an attribute from the class
			descr = get_from_type(type(TOS), method_name)
			# 90% sure this is broken in some edge cases

		except AttributeError:
			# try getting it from the dict, then do the null thing

			# ew nested try
			try:
				self.data_stack.append(None)
				self.data_stack.append(TOS.__dict__[method_name])
				return
			except KeyError:
				raise AttributeError(f"no method {method_name}")

		else:
			# working with descr here
			if isinstance(descr, FunctionType):
				# if its a method: do the good thing
				self.data_stack.append(descr)
				self.data_stack.append(TOS)
				return
			else:
				# else: do the null thing
				try:
					getter = get_from_type(type(descr), "__get__")
				except AttributeError:
					self.data_stack.append(None)
					self.data_stack.append(descr)
					return
				else:
					self.data_stack.append(None)
					self.data_stack.append(getter(descr, TOS, type(TOS)))
					return

	async def CALL_METHOD(self, argc):
		positional_arguments = []
		for i in range(argc):
			positional_arguments.insert(0, await self.POP_TOP())
		# "Below them, two items described in LOAD_METHOD on the stack"
		TOS = await self.POP_TOP()
		TOS2 = await self.POP_TOP()
		if TOS2 is None:
			method = TOS
			method_return = method(*positional_arguments)
			self.data_stack.append(method_return)
		else:
			# this branch never gets used because actually checking if it's possible
			# takes forever
			method = TOS2
			first_arg = TOS
			method_return = method(first_arg, *positional_arguments)
			self.data_stack.append(method_return)

	def __init__(self, code, name='<string>', is_function=False):
		if isinstance(code, str):
			code = compile(code, '<string>', 'exec')
		self.instruction_funcs = {
			1: self.POP_TOP,

			22: self.BINARY_MODULO,
			23: self.BINARY_ADD,
			26: self.BINARY_FLOOR_DIVIDE,

			68: self.GET_ITER,
			93: self.FOR_ITER,

			71: self.LOAD_BUILD_CLASS,

			83: self.RETURN_VALUE,
			87: self.POP_BLOCK,
			90: self.STORE_NAME,
			92: self.UNPACK_SEQUENCE,

			100: self.LOAD_CONST,
			101: self.LOAD_NAME,

			102: self.BUILD_TUPLE,
			103: self.BUILD_LIST,

			107: self.COMPARE_OP,

			108: self.IMPORT_NAME,

			110: self.JUMP_FORWARD,
			113: self.JUMP_ABSOLUTE,

			114: self.POP_JUMP_IF_FALSE,
			116: self.LOAD_GLOBAL,

			120: self.SETUP_LOOP,
			121: self.SETUP_EXCEPT,
			# 122: self.SETUP_FINALLY,

			124: self.LOAD_FAST,
			125: self.STORE_FAST,

			131: self.CALL_FUNCTION,
			132: self.MAKE_FUNCTION,

			160: self.LOAD_METHOD,
			161: self.CALL_METHOD
		}
		self.cmp_op = (
			lambda val1, val2: val1 < val2,
			lambda val1, val2: val1 <= val2,
			lambda val1, val2: val1 == val2,
			lambda val1, val2: val1 != val2,
			lambda val1, val2: val1 > val2,
			lambda val1, val2: val1 >= val2,
			lambda val1, val2: val1 in val2,
			lambda val1, val2: val1 not in val2,
			lambda val1, val2: val1 is val2,
			lambda val1, val2: val1 is not val2
		)

		self.bin_ops = {
			'+': lambda val1, val2: val1 + val2,
			'//': lambda val1, val2: val1 // val2,
			'%': lambda val1, val2: val1 % val2
		}

		self.global_variables = {

		}
		self.variables = {

		}

		self.is_function = is_function

		self.code = code
		self.co_code = code.co_code
		self.co_consts = code.co_consts
		self.co_names = code.co_names

		# Function only
		self.co_varnames = code.co_varnames
		self.references = []

		self.data_stack = []
		self.block_stack = []
		self.call_stack = []

	async def execute(self, max_steps=-1, *args):
		# self.variables = self.global_variables

		self.references = args

		self.instructions = []
		self.values = []
		for instruction, value in zip(self.co_code[::2], self.co_code[1::2]):
			self.instructions.append(instruction)
			self.values.append(value)
		self.done = False
		self.bytecode_counter = 0
		step_count = 0
		while (not self.done) and step_count != max_steps:
			await self.step()
			step_count += 1
			print(step_count)
		print('epic')
		if step_count == max_steps:
			raise ReachedMaxSteps()
		return self.returned

	async def step(self):
		print('step')
		instruction = self.instructions[self.bytecode_counter]
		value = self.values[self.bytecode_counter]
		self.bytecode_counter += 1

		# if instruction not in self.instruction_funcs:
		# 	print('! UNKNOWN INSTRUCTION', instruction, 'value:', value)
		# else:
		# 	print(self.instruction_funcs[instruction].__name__, '\t', value)
		instruction_function = self.instruction_funcs.get(
			instruction,
			lambda _: (1)
		)
		print(instruction_function, self.instructions)
		try:
			await instruction_function(value)
		except BaseException as e:
			traceback.print_exc()
			print('error!')
			# print("TODO unroll block stack here")
			raise e


async def run(message, code_arg: str):
	global output
	print('running')
	output = []
	def _print(*content, sep=' '):
		global output
		output.append(sep.join(map(str, content)))

	if code_arg.startswith('```py\n') and code_arg.endswith('```'):
		code = code_arg[6:-3]
	elif code_arg.startswith('```python\n') and code_arg.endswith('```'):
		code = code_arg[10:-3]
	else:
		code = code_arg

	i = Interpreter(code)

	i.global_variables = {
		'print': _print,
		'int': int,
		'str': str,
		'range': range,
	}

	try:
		await i.execute(max_steps=100)
	except ReachedMaxSteps:
		await message.channel.send('Too many steps :(')
		return
	except:
		await message.channel.send('Something went wrong :(')
		return

	output_joined = '\n'.join(output)
	
	if output_joined.count('\n') > 30:
		await message.channel.send('Too many lines :(')
		return

	await message.channel.send(embed=discord.Embed(
		title='Safe exec',
		description=output_joined
	))
