from __future__ import unicode_literals, division, absolute_import, print_function

from collections import deque
from pprint import pformat
import operator

try:
	StringTypes = basestring
except NameError:
	StringTypes = str

__all__ = [
	'Scope',
	
	'BinaryOp', 'TranslationUnit', 'EmptyNode',
	
	'FuncDef', 'FuncDecl', 'VariableDecl', 'Suite',
	
	'ParamSeq', 'KWArgDecl',
	
	'Stmt', 'UseStmt', 'SetStmt', 'ReturnStmt', 'IfStmt', 'WhileStmt', 'ForStmt',
	
	'NumberLiteral', 'StringLiteral', 'BoolLiteral',
	
	'GetItem', 'GetAttr', 'FuncCall', 'Assignment',
	
	'ASTException',
	
]

class ASTException(Exception):
	def __init__(self, ast = None, msg = '', *args, **kwargs):
		self.ast = ast
		self.msg = msg
		super(ASTException, self).__init__(*args, **kwargs)

class EvalException(Exception): pass

class EvalJump(Exception): pass

class EvalReturn(EvalJump):
	def __init__(self, value):
		self.value = value

class EvalContinue(EvalJump): pass
class EvalBreak(EvalJump): pass

class Scope(object):
	def __init__(self):
		self.names = {}
		self.levels = deque()
		self.levels.append([])
	
	def push(self):
		self.levels.append([])
	
	def pop(self):
		level = self.levels.pop()
		
		for name in level:
			if name in self.names:
				references = self.names[name]
				if len(references) == 1:
					del self.names[name]
				else:
					self.names[name] = references[0:]
				
	def __getitem__(self, key):
		if key not in self.names:
			raise KeyError
		
		return self.names[key][-1]
	
	def __setitem__(self, key, value):
		if key not in self.names:
			self.levels[-1].append(key)
			self.names[key] = [value]
		
		else:
			self.names[key][-1] = value
	
	def __contains__(self, name):
		return name in self.names
	
	def __enter__(self):
		self.push()
	
	def __exit__(self, exc_type, exc_value, traceback):
		self.pop()

class ASTNode(object):
	scope = Scope()
	
	def _get_tokens(self, *args, **kwargs):
		if len(args) == 1:
			return args
		elif len(args) > 1:
			return deque(args[2])
		return None
	
	def debug_print(self):
		return pformat({ self.__class__.__name__ :   { k : getattr(self, k) for k in self.__slots__} }, width = 30)
	
	def __init__(self, *args, **kwargs):
		self.ret_type = None
		
		tokens = deque(args)
		
		if tokens is None:
			for slot in self.__slots__:
				setattr(self, slot, None)
		else:
			
			for slot in self.__slots__:
				setattr(self, slot, tokens.popleft())
		
		self.__repr__ = self.__str__
		
	def __str__(self):
		return pformat({ self.__class__.__name__ :   self.__slots__ }, width = 30)

	__repr__ = __str__
	
	def __ne__(self, other):
		return not (self == other)
	
	def debug__eq__(self, other):
		ret = True
		for k in self.__slots__:
			if getattr(self, k) != getattr(other, k):
				print ("attr {} of {} != {}".format(k, self.debug_print(), other.debug_print()))
				ret = False
		return ret
	
	def __eq__(self, other):
		if not isinstance(other, self.__class__) or self.__slots__ != other.__slots__:
			return False
		
		return self.debug__eq__(other)
		
		return all([getattr(self, k) == getattr(other, k) for k in self.__slots__])

def to_str(fmt_str):
	def my__str__(self):
		return fmt_str.format(self = self)
	
	def wrapper(cls):
		cls.__str__ = my__str__
		cls.__repr__ = cls.__str__
		return cls
	return wrapper

class AcceptsList(ASTNode):
	
	def __init__(self, *args, **kwargs):
		assert len(self.__slots__) == 1
		if len(args) == 1 and isinstance(args[0], self.__class__):
			self._set_thing(args[0]._get_thing())
		else:
			new_args = list(arg for arg in args if not (isinstance(arg, (tuple, list)) and len(arg) == 0))
			self._set_thing(new_args)
	
	def eval(self, eval_context):
		for idx in xrange(len(self._get_thing())):
			try:
				self[idx].eval(eval_context)
			except EvalBreak:
				break
			except EvalContinue:
				continue
	
	def _get_thing(self):
		return getattr(self, self.__slots__[0])
	
	def _set_thing(self, thing):
		setattr(self, self.__slots__[0], thing)
	
	def __add__(self, other):
		list_thing = self._get_thing()
		
		if isinstance(list_thing, (list, tuple)):
			list_thing = list(list_thing) + [other]
		elif isinstance(other, (list, tuple)):
			list_thing = other
		else:
			list_thing = [other]
		
		self._set_thing(list_thing)
		
		return self
	
	def __iadd__(self, other):
		return self +other
	
	def __iter__(self):
		return iter(self._get_thing())
	
	def __getitem__(self, idx):
		if not isinstance(idx, int):
			raise TypeError('Index must be numeric')
		
		return self._get_thing()[idx]
	
	def __ne__(self, other):
		return not (self == other)
	
	def debug__eq__(self, other):
		ret = True
		for idx in xrange(len(self._get_thing())):
			if self[idx] != other[idx]:
				print("{} != {}".format(self[idx], other[idx]))
				ret = False
		return ret
	
	def __eq__(self, other):
		if not isinstance(other, AcceptsList) or len(self._get_thing()) != len(other._get_thing()):
			return False
		
		return self.debug__eq__(other)
		
		return all([self[idx] == other[idx] for idx in xrange(len(self._get_thing()))])

@to_str('<empty_node>')
class EmptyNode(ASTNode):
	__slots__ = ()

@to_str('TU({self.declarations!r})')
class TranslationUnit(AcceptsList):
	__slots__ = ('declarations',)
	
@to_str('{{{self.suite!r}}}')
class Suite(AcceptsList):
	__slots__ = ('suite',)
	
@to_str('{self.decl} -> {self.suite}')
class FuncDef(ASTNode):
	__slots__ = ('decl', 'suite')
	
	def eval(self, eval_context):
		self.decl.eval(eval_context)

@to_str('{self.stmt!r}')
class Stmt(ASTNode): 
	__slots__ = ('stmt',)
	def eval(self, eval_context):
		self.stmt.eval(eval_context)

@to_str('Use({self.root!r}->{self.child!r})')
class UseStmt(Stmt):
	__slots__ = ('root', 'child')
	
	def get_dotted_string(self):
		child = ''
		
		if self.child == '*':
			child = ':*'
		
		elif isinstance(self.child, UseStmt):
			child = self.child.get_dotted_string()
		
		elif isinstance(self.child, StringTypes):
			child = ':{}'.format(self.child)
		
		return '{}{}'.format(self.root, child)

@to_str('if ({self.condition}) {self.true_suite!r}{self.false_suite!r}')
class IfStmt(Stmt):
	__slots__ = ('condition', 'true_suite', 'false_suite')
	
	def eval(self, eval_context):
		condition = self.condition.eval(eval_context)
		with self.eval_context:
			try:
				if condition:
					self.true_suite.eval(eval_context)
				else:
					self.false_suite.eval(eval_context)
			except EvalReturn as e:
				return e.value

@to_str('while ({self.condition}) {self.suite!r}')
class WhileStmt(Stmt):
	__slots__ = ('condition', 'suite')
	
	def eval(self, eval_context):
		while self.condition.eval(eval_context):
			try:
				with eval_context:
					self.suite.eval(eval_context)
			except EvalContinue:
				continue
			except EvalBreak:
				break

@to_str('for ({self.expressions}) {self.suite}')
class ForStmt(Stmt):
	__slots__ = ('expressions', 'suite')
	
	def eval(self, eval_context):
		assert len(self.expressions) == 3
		
		with eval_context:
			initial_value, condition, increment = self.expressions
			initial_value.eval(eval_context)
			
			while condition.eval(eval_context):
				try:
					self.suite.eval(eval_context)
				except EvalContinue:
					increment.eval(eval_context)
					continue
				except EvalBreak:
					break
				else:
					increment.eval(eval_context)
			
@to_str('Function {self.name}({self.args})')
class FuncDecl(ASTNode):
	__slots__ = ('name', 'args')
	
	def eval(self, eval_context):
		self.args.eval(eval_context)

class ParamSeq(ASTNode):
	__slots__ = ('positional', 'has_args', 'kwargs')
	
	def __init__(self, *args, **kwargs):
		super(ParamSeq, self).__init__([], False, {})
		
		for arg in args:
			self +=arg
		
		self.kwargs.update(kwargs)
	
	def get_arg_count(self):
		if self.has_args:
			return -1
		else:
			return len(self.positional) + len(self.kwargs.keys())
		
	def __iadd__(self, other):
		if isinstance(other, VariableDecl):
			self.positional.append(other)
			
		elif isinstance(other, KWArgDecl):
			self.kwargs.update(other.kwargs)
		
		elif isinstance(other, (list, tuple)):
			for item in other:
				self +=item
		
		elif isinstance(other, ParamSeq):
			if other.has_args:
				self.has_args = True
			self.positional += other.positional
			self.kwargs.update(other.kwargs)
		else:
			raise ASTException(other, 'Tried to add incompatible ast to ParamSeq')
		
		return self
	
	def __str__(self):
		ret = ''
		
		if self.kwargs:
			ret += '[{}]'.format(', '.join('{}={!r}'.format(k, v) for k, v in self.kwargs.items()))
		
		if self.positional:
			ret += ', '.join((str(arg) for arg in self.positional))
		return ret
	
	#__repr__ = __str__
	
	
@to_str('VarDecl({self.name}, {self.initial})')
class VariableDecl(ASTNode):
	__slots__ = ('name', 'initial')
	
	def eval(self, eval_context):
		name = self.name.eval(eval_context)
		initial = self.initial.eval(eval_context)
		eval_context[name] = initial

@to_str('kwarg({self.kwargs})')
class KWArgDecl(ASTNode):
	__slots__ = ('kwargs',)

@to_str('Set({self.name}) = {self.value}')
class SetStmt(Stmt):
	__slots__ = ('name', 'value')
	
	def eval(self, eval_context):
		name = self.name.eval(eval_context)
		value = self.value.eval(eval_context)
		eval_context[name] = value

@to_str('Return({self.expr})')
class ReturnStmt(Stmt):
	__slots__ = ('expr',)
	
	def eval(self, eval_context):
		raise EvalReturn(self.expr.eval(eval_context))

@to_str('Ident({self.name})')
class Identifier(ASTNode):
	__slots__ = ('name',)
	
	def eval(self, eval_context):
		return self.name.value

@to_str('Number({self.number})')
class NumberLiteral(ASTNode):
	__slots__ = ('number',)
	
	def eval(self, eval_context):
		return self.number.value

@to_str('Bool({self.value})')
class BoolLiteral(ASTNode):
	__slots__ = ('value',)
	
	def eval(self, eval_context):
		return self.value.value

@to_str('String({self.value!r})')
class StringLiteral(ASTNode):
	__slots__ = ('value',)
	
	def eval(self, eval_context):
		return self.value.value

@to_str('RV({self.expr})')
class Expr(ASTNode):
	__slots__ = ('expr',)
	
	def eval(self, eval_context):
		return self.expr.eval(eval_context)
		
@to_str('Unary({self.op}, {self.expr})')
class UnaryOp(Expr):
	__slots__ = ('op', 'expr')
	
	def eval(self, eval_context):
		op = {
			'!' : operator.not_,
			'~' : operator.inv,
			'-' : operator.neg,
			'+' : operator.pos,
		}[self.op.value]
		
		return op(self.expr.eval(eval_context))

@to_str('Op({self.op})({self.lhs}, {self.rhs})')
class BinaryOp(Expr):
	__slots__ = ('lhs', 'op', 'rhs')
	
	def eval(self, eval_context):
		op = {
			'*' : operator.mul,
			'/' : operator.div,
			'%' : operator.mod,
			'+' : operator.add,
			'-' : operator.sub,
			'<<' : operator.lshift,
			'>>' : operator.rshift,
			'>' : operator.gt,
			'<' : operator.lt,
			'<=' : operator.le,
			'>=' : operator.ge,
			'==' : operator.eq,
			'!=' : operator.ne,
			'^'  : operator.xor,
			'&' : operator.and_,
			'|' : operator.or_,
		}[self.op.value]
		
		return op(self.lhs.eval(eval_context), self.rhs.eval(eval_context))

@to_str('{self.lhs} {self.op} {self.rhs}')
class TestOp(BinaryOp):
	def eval(self, eval_context):
		op = {
			'and' : lambda a, b: a and b,
			'or' : lambda a, b: a or b
		}[self.op.value]
		
		return op(self.lhs.eval(eval_context), self.rhs.eval(eval_context))

class Assignment(Expr):
	__slots__ = ('lhs', 'op', 'rhs')
	
	def eval(self, eval_context):
		key = self.lhs.eval(eval_context)
		
		if key not in eval_context:
			eval_context[key] = None
		
		rhs = self.rhs.eval(eval_context)
		
		if self.op.value == '=':
			eval_context[key] = rhs
		else:
			eval_context[key] = {
				'*=' : operator.imul,
				'/=' : operator.idiv,
				'%=' : operator.imod,
				'+=' : operator.iadd,
				'-=' : operator.isub,
				'&=' : operator.iand,
				'^=' : operator.ixor,
				'|=' : operator.ior,
				'<<=' : operator.ilshift,
				'>>=' : operator.irshift,
			}[self.op.value](eval_context[key], rhs)
		
		
		return eval_context[key]
		

@to_str('{self.base_expr}[{self.subscript}]')
class GetItem(Expr):
	__slots__ = ('base_expr', 'subscript')
	
	def eval(self, eval_context):
		return self.base_expr.eval(eval_context)[self.subscript.eval(eval_context)]

@to_str('{self.base_expr}[{self.substcript}]')
class GetAttr(Expr):
	__slots__ = ('base_expr', 'subscript')
	
	def eval(self, eval_context):
		return getattr(self.base_expr.eval(eval_context), self.subscript.eval(eval_context))

@to_str('{self.fn_name}({self.params})')
class FuncCall(Expr):
	__slots__ = ('fn_name', 'params')
	
	def eval(self, eval_context):
		if self.fn_name not in eval_context:
			raise EvalException("Could not find function {} in eval context".format(self.fn_name))
		
		fn = eval_context[self.fn_name]
		
		suite = fn.suite
		
		with eval_context:
			for p in self.params:
				param = p.eval(eval_context)
				eval_context[param.name] = param
			suite.eval(eval_context)

class Trailer(Expr):
	__expr__ = ('expr', 'trailer')
	def __str__(self): return 'Sub({}[{}])'.format(self.expr, self.trailer)
