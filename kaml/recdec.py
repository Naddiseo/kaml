from __future__ import unicode_literals, division, absolute_import, print_function

from kaml.lexer import Lexer
from kaml.astnodes import * #@UnusedWildImport
from kaml.package_import import PackageImporter
from kaml.astnodes import UnaryOp

class ParseError(Exception): pass
class KAMLSyntaxError(ParseError): pass

class Parser(object):
	
	def __init__(self, *args, **kwargs):
		self.lexer = Lexer()
		self.la = self.lexer.la
		self.skip = self.lexer.skip
		
		self.scope = Scope()
		self.importer = PackageImporter(
			kwargs.get('search_paths', ['.']),
			parser_kwargs = dict(
				debug = kwargs.get('debug', False)
			),
			memo = kwargs.get('importer_memo', set())
		)
		
	def t(self, filter_ws = True):
		return self.lexer.token(filter_ws)
	
	def expect(self, tok_type, tok_value = None, filter_ws = True):
		tok = self.t(filter_ws)
		return self.shouldbe(tok, tok_type, tok_value)
	
	def shouldbe(self, tok, tok_type, tok_value = None):
		if tok.type == tok_type:
			if tok_value is None or (tok_value is not None and tok.value == tok_value):
				if tok.value is None:
					return tok
				else:
					return tok.value
		
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
			if top_level_block_item is None:
				break
			items.append(top_level_block_item)
		
		if len(items):
			return TranslationUnit(*items)
		
		return EmptyNode()
	
	def top_level_block_item(self):
		la = self.la()
		
		if la is None:
			return None
		elif la.type == 'USE':
			return self.use_stmt()
		elif la.type == 'DEF':
			return self.func_defn()
		else:
			return self.block_item()
	
	def use_stmt(self):
		self.expect('USE')
		use = UseStmt(self.expect('ID'), self.package_import())
		self.expect(';')
		ast = self.importer.import_package(use.get_dotted_string())
		# TODO: resolve names from the import
		return ast
	
	def package_import(self):
		la = self.la()
		if la.type == ':':
			self.expect(':')
			child = self.t()
			if child.type == '*':
				return self.expect('*')
			else:
				return UseStmt(self.shouldbe(child, 'ID'), self.package_import())
		return None
	
	def func_defn(self):
		
		decl = self.function_decl()
		
		self.scope.push()
		body = self.function_body()
		self.scope.pop
		
		return FuncDef(decl, body)
	
	def function_decl(self):
		self.expect('DEF')
		
		la = self.la()
		compile_time = False
		
		if la.type == 'ID':
			fn_name = self.expect('ID')
		
		elif la.type == 'STRING_LIT':
			# Compile time functions
			fn_name = self.t().value
			compile_time = True
			
		
		params = self.function_params()
		
		decl = FuncDecl(fn_name, params, compile_time = compile_time)
		self.scope[fn_name] = decl
		
		return decl
	
	def function_params(self):
		params = ParamSeq()
		
		while True:
			p = self.param_def()
			if p is None:
				break
			else:
				params += p
				self.lexer.untoken(self.list_sep(True))
				
		
		return params
	
	def param_def(self):
		l = self.la()
		
		if l.type == 'ID':
			# Could be param name, or a function call
			param_name = self.expect('ID')
			if param_name in self.scope and isinstance(self.scope[param_name], FuncDef):
				
				fn = self.scope[param_name]
				if fn.is_compile_time:
					return self.call_compiled_function(fn)
				else:
					raise KAMLSyntaxError("Tried to call a function <{}> that is not compile time".format(param_name))
			
			else:
				if self.la().type == '=':
					self.expect('=')
					return VariableDecl(param_name, self.expression())
				else:
					return VariableDecl(param_name, None)
		
		elif l.value in self.scope and isinstance(self.scope[l.value], FuncDef):
			# Could be a symbol function
			t = self.t()
			fn = self.scope[t.value]
			if fn.is_compile_time:
				return self.call_compiled_function(fn)
			else:
				raise KAMLSyntaxError("Tried to call a function <{}> that is not compile time".format(t))
		
		return None
				
				
	def function_body(self):
		self.expect('{')
		b = Suite()
		
		while self.la().type != '}':
			s = self.block_item()
			if s is None:
				break
			b += s
		
		self.expect('}')
		
		return b
	
	def block_item(self):
		''' statement : expression-statement
		              | compound-statement
		              | selection-statement
		              | jump-statement
		              | declaration-statement
		              | loop-statement
		              | set-statement
		'''
		
		l = self.la()
		
		stmt_fn = {
			'SET' : self.set_stmt,
			'IF' : self.if_stmt,
			'WHILE' : self.while_stmt,
			'FOR' : self.for_stmt,
			'RETURN' : self.return_stmt,
			'BREAK' : self.break_stmt,
			'CONTINUE' : self.continue_stmt,
			
		}
		
		return stmt_fn.get(l.type, self.expression)()
	
	def set_stmt(self):
		self.expect('SET')
		target = self.expect('ID')
		self.expect('=')
		expr = self.expression()
		self.semi_or_nl()
		return SetStmt(target, expr)
	
	def if_stmt(self):
		self.expect('IF')
		return IfStmt()
	
	def while_stmt(self):
		self.expect('WHILE')
		return WhileStmt()
	
	def for_stmt(self):
		self.expect('FOR')
		return ForStmt()
	
	def return_stmt(self):
		self.expect('RETURN')
		expr = self.expression()
		self.semi_or_nl()
		return ReturnStmt(expr)
	
	def break_stmt(self):
		self.expect('BREAK')
		return self.break_stmt()
	
	def continue_stmt(self):
		self.expect('CONTINUE')
		return ContinueStmt()
	
	def stmt(self):
		return None
	
	def expression(self):
		''' assignment-expression : conditional-expression
		                          | or-test assignment-operator assignment-expression
		'''
		return self.conditional_expression()
	
	def literal(self):
		''' literal : integer-literal
		            | floating-literal
		            | string-literal
		            | boolean-literal
		'''
		tp = self.la().type
		l = {
			'INT_LIT' : NumberLiteral,
			'FLOAT_LIT' : NumberLiteral,
			'STRING_LIT' : StringLiteral,
			'TRUE' : BoolLiteral,
			'FALSE' : BoolLiteral
		}
		if tp in l:
			return l[tp](self.t().value)
		return None
	
	def primary_expression(self):
		'''
		primary-expression : literal
		                   | ID
		'''
		if self.la().type == 'ID':
			return self.expect('ID')
		else:
			return self.literal()
	
	def postfix_expression(self):
		'''
		postfix-expression : primary-expression
		                   | postfix-expression '[' conditional-expr-list  ']'
		                   | postfix-expression hash-param-opt dot-param-opt kwarg-param-opt '(' expression-list-opt ')'
		                   | postfix-expression SCOPEDID
		                   | '(' expression ')'
		'''
		if self.la().type == '(':
			self.expect('(')
			expr = self.expression()
			self.expect(')')
			return expr
		return self.primary_expression()
	
	# TODO: test this right recursion
	def unary_expression(self):
		''' unary-expression : postfix-expression
		                     | unary-operator unary-expression %prec UMINUS
		'''
		if self.la().type in ('+', '-', '!', '~'):
			return UnaryOp(self.t(), self.postfix_expression())
		return self.postfix_expression()
	
	def multiplicative_expression(self):
		''' multiplicative-expression : unary-expression
		                              | multiplicative-expression '*' unary-expression
		                              | multiplicative-expression '/' unary-expression
		                              | multiplicative-expression '%' unary-expression
		'''
		expr = self.unary_expression()
		if self.la().type in ('*', '/', '%'):
			return BinaryOp(expr, self.t(), self.unary_expression())
		return expr
	
	def additive_expression(self):
		''' additive-expression : multiplicative-expression
		                        | additive-expression '+' multiplicative-expression
		                        | additive-expression '-' multiplicative-expression 
		'''
		expr = self.multiplicative_expression()
		if self.la().type in ('+', '-'):
			return BinaryOp(expr, self.t(), self.additive_expression())
		return expr
	
	def shift_expression(self):
		''' shift-expression : additive-expression
		                     | shift-expression SHL additive-expression
		                     | shift-expression SHR additive-expression   
		'''
		expr = self.additive_expression()
		if self.la().type in ('SHR', 'SHL'):
			return BinaryOp(expr, self.t(), self.additive_expression())
		return expr
	
	def relational_expression(self):
		''' relational-expression : shift-expression
		                          | relational-expression '<' shift-expression
		                          | relational-expression '>' shift-expression
		                          | relational-expression LTE shift-expression
		                          | relational-expression GTE shift-expression
		'''
		expr = self.shift_expression()
		if self.la().type in ('<', '>', 'LTE', 'GTE'):
			return BinaryOp(expr, self.t(), self.shift_expression())
		return expr
	
	def equality_expression(self):
		''' equality-expression : relational-expression
		                        | equality-expression EQ relational-expression
		                        | equality-expression NE relational-expression
		'''
		expr = self.relational_expression()
		if self.la().type in ('EQ', 'NE'):
			return BinaryOp(expr, self.t(), self.relational_expression())
		return expr
	
	def and_expression(self):
		''' and-expression : equality-expression
		                   | and-expression '&' equality-expression
		'''
		expr = self.equality_expression()
		if self.la().type == '&':
			return BinaryOp(expr, self.expect('&'), self.equality_expression())
		return expr
	
	def xor_expression(self):
		''' xor-expression : and-expression
		                   | xor-expression '^' and-expression 
		'''
		expr = self.and_expression()
		if self.la().type == '^':
			return BinaryOp(expr, self.expect('^'), self.and_expression())
		return expr
	
	def or_expression(self):
		''' or-expression : xor-expression
		                  | or-expression '|' xor-expression 
		'''
		expr = self.xor_expression()
		if self.la().type == '|':
			return BinaryOp(expr, self.expect('|'), self.xor_expression())
		return expr
	
	def and_test(self):
		''' and-test : or-expression
		             | and-test AND or-expression
		'''
		expr = self.or_expression()
		if self.la().type == 'AND':
			return TestOp(expr, self.expect('AND'), self.or_expression())
		return expr
	
	# TODO: test this right recursion
	def or_test(self):
		''' or-test : and-test
		            | and-test OR or-test
		'''
		
		expr = self.and_test()
		if self.la().type == 'OR':
			return TestOp(expr, self.expect('OR'), self.or_test())
		return expr
	
	def conditional_expression(self):
		''' conditional-expression : or-test
		                           | or-test '?' expression ':' assignment-expression
		'''
		
		condition = self.or_test()
		
		if self.la().type == '?':
			self.expect('?')
			true_block = Suite(self.expression())
			self.expect(':')
			false_block = Suite(self.expression())
			return IfStmt(condition, true_block, false_block)
		else:
			return condition
	
	def call_compiled_function(self, fn):
		self.scope.push()
		ast = fn.call(self.scope)
		self.scope.pop()
		return ast
	
	def semi_or_nl(self):
		la = self.la(False)
		if la.type == ';':
			return self.t()
		if la.type == 'WS' and '\n' in la.value:
			return self.t()
		raise KAMLSyntaxError("Expecting ';'")
	
	def list_sep(self, could_be_end = False):
		''' \s*(,)?\s*'''
		sep = False
		t = self.t(False)
		while t.type == 'WS':
			sep = True
			t = self.t(False)
		
		if t.type == ',':
			sep = True
			t = self.t(False)
		
		while t.type == 'WS':
			sep = True
			t = self.t(False)
		
		if not sep and not could_be_end:
			raise KAMLSyntaxError('Expected a list separator WS or "," but got <{}>'.format(t))
		
		return t
