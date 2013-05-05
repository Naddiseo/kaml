from ply import yacc

from kaml.lexer import Lexer
from astnodes import EmptyNode
from kaml.astnodes import Suite

class Parser(object):
	
	def __init__(self, *args, **kwargs):
		self.lexer = Lexer()
		self.tokens = self.lexer.tokens
		
		self.parser = yacc.yacc(module = self, *args, **kwargs)
	
	def parse(self, data, debug = 0, tracking = 0):
		if not data:
			return []
		
		return self.parser.parse(data, self.lexer.lexer, debug, tracking, None)
	
	
	start = 'translation-unit'
	precedence = (
		('left', ','),
		('right', '?', ':', '=', 'ADDEQ', 'SUBEQ', 'MULEQ', 'DIVEQ', 'MODEQ', 'SHLEQ', 'SHREQ', 'ANDEQ', 'XOREQ', 'OREQ'),
		('left', 'OR'),
		('left', 'AND'),
		('left', '|'),
		('left', '^'),
		('left', '&'),
		('left', 'EQ'),
		('left', 'NE'),
		('left', '<', 'LTE', '>', 'GTE'),
		('left', 'SHL', 'SHR'),
		('left', '-', '+'),
		('left', '*', '/', '%'),
		('right', 'UMINUS'),
		('left', '.'),
		('left', 'INC', 'DEC')
	)
	
	def p_error(self, p):
		print('Parser Error: {}'.format(p))
	
	def p_translation_unit(self, p):
		''' translation-unit :
		                     | top-level-list
		'''
		
		if len(p) > 1:
			p[0] = p[1]
		else:
			p[0] = EmptyNode()
	
	def p_top_level_list(self, p):
		''' top-level-list : top-level-item
		                   | top-level-list top-level-item
		'''
		if len(p) == 2:
			p[0] = [p[1]]
		else:
			p[0] = p[1] + [p[0]]
	
	def p_top_level_item(self, p):
		''' top-level-item : string-expression
		                   | statement
		'''
	
	def p_statement(self, p):
		''' statement : expression-statement
		              | compound-statement
		              | selection-statement
		              | jump-statement
		              | set-statement
		              | declaration-statement
		'''
		p[0] = p[1]
	
	def p_expression_statement(self, p):
		''' expression-statement : expression ';'
		'''
		p[0] = p[1]
	
	def p_compound_statement(self, p):
		''' compound-statement : '{' top-level-list '}'
		                       | '{' '}'
		'''
		p[0] = Suite([] if len(p) == 3 else p[2])
	
	def p_selection_statement(self, p):
		''' selection-statement : IF '(' expression ')' compound-statement selection-statement-tail
		'''
	
	def p_selection_statement_tail(self, p):
		''' selection-statement-tail : ELIF '(' expression ')' compound-statement selection-statement-tail
		                             | ELSE compound-statement
		'''
	
	def p_jump_statement(self, p):
		''' jump-statement : RETURN expression ';'
		                   | RETURN ';'
		'''
	
	def p_set_statement(self, p):
		''' set-statement : SET assignment-expression ';'
		'''
	
	def p_declaration_statement(self, p):
		''' declaration-statement : function-definition
		'''
