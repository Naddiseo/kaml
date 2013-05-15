from __future__ import unicode_literals

from kaml.lexer import Lexer
from kaml.astnodes import * #@UnusedWildImport

class ParseError(Exception): pass
class KAMLSyntaxError(ParseError): pass

class Parser(object):
	
	def __init__(self, *args, **kwargs):
		self.lexer = Lexer()
		self.la = self.lexer.la
		self.skip = self.lexer.skip
		
	def t(self, filter_ws = True):
		t = self.lexer._get_token()
		if filter_ws:
			while t.type == 'WS':
				t = self.lexer._get_token()
		
		return t 
	
	def expect(self, tok_type, tok_value = None, filter_ws = True):
		tok = self.t(filter_ws)
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
		return UseStmt(self.expect('ID'), self.package_import())
	
	def package_import(self):
		la = self.la(1)
		if la.type in ('ID', ':'):
			child = self.t()
			if child.type == ':':
				return self.expect('*')
			else:
				return UseStmt(self.shouldbe(child, 'ID'), self.package_import())
		
		elif la.type == ';':
			self.expect(';')
			return None
		
		raise KAMLSyntaxError(la)
	
	def func_defn(self):
		return FuncDef(
			self.function_decl(),
			self.function_body()
		)
	
	def function_decl(self):
		self.expect('DEF')
		
		fn_name = self.expect('ID')
		
		return FuncDecl(fn_name, None)
	
	def function_body(self):
		pass
	
	def stmt(self):
		return None
