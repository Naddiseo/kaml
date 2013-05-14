from __future__ import unicode_literals

from kaml.lexer import Lexer
from kaml.astnodes import * #@UnusedWildImport

class ParseError(Exception): pass

class Parser(object):
	
	def __init__(self, *args, **kwargs):
		self.lexer = Lexer()
		self.token_stack = []
		self.la = self.lexer.la
		self.skip = self.lexer.skip
		
	def t(self):
		if len(self.token_stack):
			return self.token_stack.pop()
		return self.lexer._get_token()
	
	def expect(self, tok_type, tok_value = None):
		tok = self.t()
		return self.shouldbe(tok, tok_type, tok_value)
		
	
	def shouldbe(self, tok, tok_type, tok_value = None):
		if tok.type == tok_type:
			if tok_value is None or (tok_value is not None and tok.value == tok_value):
				return tok
		
		raise ParseError("Expecting Tok<{}>({}) but got {}".format(tok_type, tok_value, tok))
	
	def parse(self, data, debug = 0, tracking = 0):
		if not data:
			return []
		self.lexer.set_data(data)
		
		return self.translation_unit()
	
	def translation_unit(self):
		items = []
		
		while True:
			top_level_block_item = self.top_level_block_item()
			if not top_level_block_item:
				break
			items.append(top_level_block_item)
		
		
		if len(items):
			return TranslationUnit(*items)
		
		return EmptyNode()
	
	def top_level_block_item(self):
		la = self.la(1)
		
		if la.type == 'USE':
			return self.use_stmt()
		elif la.type == 'DEF':
			return self.func_defn()
		else:
			return self.stmt()
	
	def use_stmt(self):
		self.expect('USE')
		ret = self.expect('ID')
		
		while self.la(1).type == ':':
			self.skip(1)
			child = self.t()
			if child.type == '*':
				ret = UseStmt(ret, child)
				break
			elif child.type == ';':
				break
			else:
				self.shouldbe(child, 'ID')
				ret = UseStmt(ret, child)
		
		return ret
	
	def func_defn(self):
		return None
	
	def stmt(self):
		return None
