from collections import deque
from pprint import pformat

__all__ = [
	'Node', 'BinaryOp', 'TranslationUnit', 'EmptyNode',
	
	'FuncDef', 'FuncDecl', 'VariableDecl', 'Suite',
	
	'ParamSeq', 'KWArgDecl', 'HashDecl', 'DotDecl',
	
	'Stmt', 'UseStmt', 'SetStmt', 'ReturnStmt', 'IfStmt', 'WhileStmt', 'ForStmt',
	
	'NumberLiteral', 'StringLiteral', 'BoolLiteral',
	
	'GetItem', 'GetAttr', 'FuncCall', 'Assign',
	
	'ASTException',
	
]

class ASTException(Exception):
	def __init__(self, ast = None, msg = '', *args, **kwargs):
		self.ast = ast
		self.msg = msg
		super(ASTException, self).__init__(*args, **kwargs)

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

class Node(object):
	def __init__(self, node_type, children = None, leaf = None):
		self.node_type = node_type
		if children:
			self.children = children
		else:
			self.children = []
		self.leaf = leaf
	
	def __repr__(self):
		return '{}{}'.format(self.node_type, self.children)

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
	
	def accepts(self, visitor):
		visitor.visit_translation_unit()
		
		for declaration in self.declarations:
			declaration.accepts(visitor)

@to_str('{{{self.suite!r}}}')
class Suite(AcceptsList):
	__slots__ = ('suite',)
	
	def accepts(self, visitor):
		self.scope.push()
		for item in self.suite:
			item.verify()
		
		self.scope.pop()

@to_str('{self.decl} -> {self.suite}')
class FuncDef(ASTNode):
	__slots__ = ('decl', 'suite')
	
	
@to_str('{self.stmt!r}')
class Stmt(ASTNode): 
	__slots__ = ('stmt',)

@to_str('Use({self.root!r}->{self.child!r})')
class UseStmt(Stmt):
	__slots__ = ('root', 'child')

@to_str('if ({self.condition}) {self.true_suite!r}{self.false_suite!r}')
class IfStmt(Stmt):
	__slots__ = ('condition', 'true_suite', 'false_suite')

@to_str('while ({self.condition}) {self.suite!r}')
def WhileStmt(Stmt):
	__slots__ = ('condition', 'suite')

@to_str('for ({self.expressions}) {self.suite}')
def ForStmt(Stmt):
	__slots__ = ('expressions', 'suite')

@to_str('Function {self.name}({self.args})')
class FuncDecl(ASTNode):
	__slots__ = ('name', 'args')

class ParamSeq(ASTNode):
	__slots__ = ('positional', 'hash_arg', 'dot_args', 'kwargs')
	
	def __init__(self, *args, **kwargs):
		if not args:
			args = []
		if not kwargs:
			kwargs = {}
		super(ParamSeq, self).__init__(args, None, None, kwargs)
	
	def add_positional(self, arg):
		self.positional.append(arg)
	
	def __iadd__(self, other):
		if isinstance(other, VariableDecl):
			self.positional.append(other)
			
		elif isinstance(other, KWArgDecl):
			self.kwargs.update(other.kwargs)
		
		elif isinstance(other, HashDecl):
			if self.has_arg is not None:
				raise ASTException(other, 'Node already has a hash_arg')
			self.has_arg = other
		
		elif isinstance(other, DotDecl):
			if self.dot_args is None:
				self.dot_args = []
			
			self.dot_args.append(other)
		
		elif isinstance(other, (list, tuple)):
			for item in other:
				self +=item
		
		else:
			raise ASTException(other, 'Tried to add incompatible ast to ParamSeq')
		
		return self
	
	def __str__(self):
		ret = ''
		if self.hash_arg is not None:
			ret += '#{}'.format(self.hash_arg)
		if self.dot_args is not None and len(self.dot_args):
			ret += '.' + '.'.join((arg for arg in self.dot_args))
		
		if self.kwargs:
			ret += '[{}]'.format(', '.format('{}={!r}'.format(k, v) for k, v in self.kwargs.items()))
		
		if self.positional:
			ret += ', '.join((str(arg) for arg in self.positional))
		return ret
	
	#__repr__ = __str__
	
	
@to_str('Var({self.name}, {self.initial})')
class VariableDecl(ASTNode):
	__slots__ = ('name', 'initial')

@to_str('kwarg({self.kwargs})')
class KWArgDecl(ASTNode):
	__slots__ = ('kwargs',)

@to_str('HashDecl({self.name})')
class HashDecl(ASTNode):
	__slots__ = ('name',)

@to_str('DotDecl({self.name})')
class DotDecl(ASTNode):
	__slots__ = ('name',)

@to_str('Set({self.name}) = {self.value}')
class SetStmt(Stmt):
	__slots__ = ('name', 'value')

@to_str('Return({self.expr})')
class ReturnStmt(Stmt):
	__slots__ = ('expr',)

@to_str('Ident({self.name})')
class Identifier(ASTNode):
	__slots__ = ('name',)

@to_str('Number({self.number})')
class NumberLiteral(ASTNode):
	__slots__ = ('number',)

@to_str('Bool({self.value})')
class BoolLiteral(ASTNode):
	__slots__ = ('value',)

@to_str('String({self.value!r})')
class StringLiteral(ASTNode):
	__slots__ = ('value',)

@to_str('Character({self.value!r}')
class CharacterLiteral(ASTNode):
	__slots__ = ('value',)

@to_str('RV({self.expr})')
class Expr(ASTNode):
	__slots__ = ('expr',)
		
@to_str('Unary({self.op}, {self.expr})')
class UnaryOp(Expr):
	__slots__ = ('op', 'expr')

@to_str('Op({self.op})({self.lhs}, {self.rhs})')
class BinaryOp(Expr):
	__slots__ = ('lhs', 'op', 'rhs')

@to_str('Assign({self.lhs} -> {self.rhs})')
class Assign(BinaryOp): pass

@to_str('Rel({self.lhs} {self.op} {self.rhs})')
class RelationOp(BinaryOp): pass

@to_str('{self.base_expr}[{self.substcript}]')
class GetItem(Expr):
	__slots__ = ('base_expr', 'subscript')
	
@to_str('{self.base_expr}[{self.substcript}]')
class GetAttr(Expr):
	__slots__ = ('base_expr', 'subscript')

@to_str('{self.fn_name}({self.params})')
class FuncCall(Expr):
	__slots__ = ('fn_name', 'params')

class Trailer(Expr):
	__expr__ = ('expr', 'trailer')
	def __str__(self): return 'Sub({}[{}])'.format(self.expr, self.trailer)
