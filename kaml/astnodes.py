from collections import deque
from pprint import pformat

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
	
	def __eq__(self, other):
		if not isinstance(other, self.__class__) or self.__slots__ != other.__slots__:
			return False
		
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
	
	def __eq__(self, other):
		if not isinstance(other, AcceptsList) or len(self._get_thing()) != len(other._get_thing()):
			return False
		
		return all([self[idx] == other[idx] for idx in xrange(len(self._get_thing()))])

@to_str('<empty_node>')
class EmptyNode(ASTNode):
	__slots__ = ()

@to_str('{self.items!r}')
class TranslationUnit(AcceptsList):
	__slots__ = ('items',)
	
	def accepts(self, visitor):
		visitor.visit_translation_unit()
		
		for item in self.items:
			item.accepts(visitor)

class Suite(AcceptsList): pass
