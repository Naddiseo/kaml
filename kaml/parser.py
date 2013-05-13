from __future__ import unicode_literals
import itertools

from ply import yacc

from kaml.lexer import Lexer
from kaml.astnodes import * 

class ParseException(Exception):pass

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
		('left', '.', '#'),
	)
	
	def _binary_op(self, p):
		if len(p) == 2:
			p[0] = p[1]
		else:
			p[0] = BinaryOp(p[1], p[2], p[3])
	
	def _flatten(self, list_thing):
		if isinstance(list_thing, (list, tuple)):
			return list(itertools.chain.from_iterable(list_thing))
		return list_thing
	
	def p_error(self, p):
		if p is not None:
			loc = self.lexer._make_tok_location(p)
			print('Parser Error[{}:{}]: {}'.format(loc[0], loc[1], p))
			raise ParseException('Parser Error[{}:{}]: {}'.format(loc[0], loc[1], p))
		else:
			print("Parser Error, inserting ';'")
			# Just guess, and hope that the error occurred in a statement
			return ';'
	
	def p_translation_unit(self, p):
		''' translation-unit : 
		                     | top-level-block-items
		
		'''
		if len(p) > 1:
			p[0] = TranslationUnit(*p[1])
		else:
			p[0] = EmptyNode()
		
	def p_top_level_block_seq(self, p):
		''' top-level-block-items : top-level-block-item
		                   | top-level-block-items top-level-block-item
		'''
		if len(p) == 2:
			p[0] = [p[1]]
		else:
			p[0] = p[1] + [p[2]]
	
	def p_top_level_block_item(self, p):
		''' top-level-block-item : use-statement
		                         | function-definition
		                         | statement
		'''
		p[0] = p[1]
	
	def p_use_statement(self, p):
		''' use-statement : USE package-import ';'
		                  | USE package-import ':' '*' ';'
		'''
		if len(p) == 4:
			if isinstance(p[2], UseStmt):
				p[0] = p[2]
			else:
				p[0] = UseStmt(p[2], '')
		else:
			p[0] = UseStmt(p[2], p[4])
	
	def p_package_import(self, p):
		''' package-import : ID 
		                   | package-import ':' ID
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			p[0] = UseStmt(p[1], p[3])
		
	def p_function_definition(self, p):
		''' function-definition : function-decl function-body
		'''
		p[0] = FuncDef(p[1], p[2])
	
	def p_function_decl(self, p):
		''' function-decl : DEF ID hash-param-opt dot-param-opt kwarg-param-opt positional-params-opt
		'''
		seq = p[6]
		assert type(seq) == ParamSeq
		
		seq += p[3]
		seq += p[4]
		seq += p[5]
		
		p[0] = FuncDecl(p[2], seq)
	
	def p_function_positional_params_opt(self, p):
		''' positional-params-opt : 
		                          | '(' parameter-decl-seq ')'
		'''
		
		if len(p) > 1:
			p[0] = p[2]
		else:
			p[0] = ParamSeq()
	
	def p_function_body(self, p):
		''' function-body : compound-statement 
		'''
		p[0] = p[1]
	
	def p_kwarg_param_opt(self, p):
		''' kwarg-param-opt :
		                    | kwarg-param-decl
		'''
		if len(p) > 1:
			p[0] = p[1]
		else:
			p[0] = []
	
	def p_hash_param_opt(self, p):
		''' hash-param-opt :
		                    | hash-param-decl
		'''
		if len(p) > 1:
			p[0] = p[1]
		else:
			p[0] = []
	
	def p_dot_param_opt(self, p):
		''' dot-param-opt :
		                    | dot-param-decl dot-param-opt
		'''
		if len(p) > 1:
			p[0] = [p[1]] + p[2]
		else:
			p[0] = []
	
	# It's not right recursion that caused this to fail,
	# but without the second rule it would require the first
	# parameter to always be followed by a comma.
	def p_parameter_decl_seq(self, p):
		''' parameter-decl-seq :
		                       | parameter-decl-list
		'''
		
		s = ParamSeq() if not isinstance(p[0], ParamSeq) else p[0]
		
		try:
			if len(p) > 1:
				s += p[1]
		except ASTException as e:
			raise ParseException(e.ast, e.msg)
		
		p[0] = s
	
	def p_parameter_decl_list(self, p):
		''' parameter-decl-list : parameter-decl optional-assign
		                        | parameter-decl optional-assign ',' parameter-decl-seq
		'''
		s = ParamSeq() if not isinstance(p[0], ParamSeq) else p[0]
		
		s += VariableDecl(p[1], p[2])
		
		if len(p) == 5:
			s += p[4]
		
		p[0] = s
	
	def p_kwarg_param_decl(self, p):
		''' kwarg-param-decl : '[' parameter-decl-seq ']'
		'''
		p[0] = KWArgDecl({ v.name : v.initial for v in p[2].positional })
		
	def p_hash_param_decl(self, p):
		''' hash-param-decl : '#' ID
		'''
		p[0] = HashDecl(p[2])
	
	def p_dot_param_decl(self, p):
		''' dot-param-decl : '.' ID
		'''
		p[0] = DotDecl(p[2])
	
	def p_parameter_decl(self, p):
		''' parameter-decl : ID
		'''
		p[0] = p[1]
	
	def p_optional_assign(self, p):
		'''
		optional-assign :
		                | '=' assignment-expression
		'''
		if len(p) == 1:
			p[0] = []
		else:
			p[0] = p[2]
	
	def p_compound_statement(self, p):
		''' compound-statement : '{' statement-seq '}' 
		                       | '{' '}'
		'''
		if len(p) == 3:
			p[0] = Suite([])
		else:
			p[0] = Suite(p[2])
	
	def p_statement_seq(self, p):
		''' statement-seq : statement
		                  | statement-seq statement
		'''
		if len(p) == 2:
			p[0] = Suite(p[1])
		else:
			p[0] = p[1] + p[2]
	
	def p_statement(self, p):
		''' statement : expression-statement
		              | compound-statement
		              | selection-statement
		              | jump-statement
		              | declaration-statement
		              | loop-statement
		              | set-statement
		'''
		p[0] = p[1]
	
	def p_set_statement(self, p):
		''' set-statement : SET assignment-expression ';'
		'''
		p[0] = SetStmt(p[2])
	
	def p_loop_statement(self, p):
		''' loop-statement : for-loop
		                   | while-loop
		'''
		p[0] = p[1]
	
	def p_for_loop(self, p):
		''' for-loop : FOR '(' expression-list ')' compound-statement 
		'''
		p[0] = ForStmt(p[3], p[5])
	
	def p_while_loop(self, p):
		''' while-loop : WHILE '(' expression ')' compound-statement
		'''
		p[0] = WhileStmt(p[2], p[4])
	
	def p_expression_statement(self, p):
		''' expression-statement : expression ';'
		'''
		p[0] = Stmt(p[1])
	
	def p_jump_statement(self, p):
		''' jump-statement : RETURN expression ';'
		                   | RETURN ';'
		                   | BREAK ';'
		                   | CONTINUE ';'
		'''
		if len(p) == 3:
			p[0] = ReturnStmt(None)
		else:
			p[0] = ReturnStmt(p[2])
	
	def p_selection_statement(self, p):
		''' selection-statement : IF '(' expression ')' compound-statement selection-statement-tail
		'''
		p[0] = IfStmt(p[3], p[5], p[6])
	
	def p_selection_statement_tail(self, p):
		''' selection-statement-tail : ELIF '(' expression ')' compound-statement selection-statement-tail
		                             | ELSE compound-statement
		                             |
		'''
		if len(p) == 1:
			p[0] = None
		elif len(p) == 3:
			p[0] = p[2]
		else:
			p[0] = IfStmt(p[4], p[6], p[7])
	
	def p_declaration_statement(self, p):
		''' declaration-statement : block-declaration
		'''
		p[0] = Stmt(p[1])
	
	def p_block_declaration(self, p):
		''' block-declaration : ID '=' assignment-expression ';'
		'''
		p[0] = VariableDecl(p[1], p[3])
		
	def p_literal(self, p):
		''' literal : integer-literal
		            | floating-literal
		            | string-literal
		            | boolean-literal
		'''
		p[0] = p[1]
	
	def p_integer_literal(self, p):
		''' integer-literal : INT_LIT
		'''
		p[0] = NumberLiteral(p[1])
		p[0].ret_type = int
	
	def p_floating_literal(self, p):
		''' floating-literal : FLOAT_LIT'''
		p[0] = NumberLiteral(p[1])
		p[0].ret_type = float
	
	def p_string_literal(self, p):
		''' string-literal : STRING_LIT 
		                   | string-literal STRING_LIT
		'''
		if len(p) == 2:
			p[0] = StringLiteral(p[1])
			p[0].ret_type = str
		else:
			if p[0] is not None:
				p[0].value += p[2].value
			else:
				if isinstance(p[1], StringLiteral):
					p[1].value += p[2]
					p[0] = p[1]
				else:
					p[0] = StringLiteral(p[2])
	
	def p_boolean_literal(self, p):
		''' boolean-literal : TRUE
		                    | FALSE
		'''
		p[0] = BoolLiteral(p[1] == 'TRUE')
		p[0].ret_type = bool
	
	def p_primary_expression(self, p):
		'''
		primary-expression : literal
		                   | ID
		'''
		p[0] = p[1]
	
	def p_postfix_expression(self, p):
		'''
		postfix-expression : primary-expression
		                   | postfix-expression '[' conditional-expr-list  ']'
		                   | postfix-expression hash-param-opt dot-param-opt kwarg-param-opt '(' expression-list-opt ')'
		                   | postfix-expression SCOPEDID
		                   | '(' expression ')'
		'''
		lp = len(p)
		
		if lp == 2:
			p[0] = p[1]
		elif lp == 5:
			ast_note_type = {
				'{' : GetItem,
				'(' : FuncCall
			}[p[2]]
			
			p[0] = ast_note_type(p[1], p[3])
		
		elif lp == 4:
			if p[1] == '(':  # '(' expression ')'
				p[0] = p[2]
			else:
				p[0] = GetAttr(p[1], p[3])
		
		else:
			raise Exception('Unknown structure for postfix expression {!r}, {}'.format(p, len(p)))
		
	def p_expression_list_opt(self, p):
		''' expression-list-opt : expression-list
		                        |
		'''
		p[0] = p[1]
	
	def p_expression_list(self, p):
		''' expression-list : assignment-expression
		                    | expression-list ',' assignment-expression
		'''
		if len(p) == 2:
			p[0] = p[1]
		
		else:
			if isinstance(p[1], (list, tuple)):
				p[0] = list(p[1]) + [p[3]]
			else:
				p[0] = [p[1], p[3]]
	
	# TODO: test this right recursion
	def p_unary_expression(self, p):
		''' unary-expression : postfix-expression
		                     | unary-operator unary-expression %prec UMINUS
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			p[0] = Node('UnaryOp', [p[1], p[2]])
	
	def p_unary_operator(self, p):
		''' unary-operator : '+'
		                   | '-'
		                   | '!'
		                   | '~'
		'''
		p[0] = p[1]
	
	def p_multiplicative_expression(self, p):
		''' multiplicative-expression : unary-expression
		                              | multiplicative-expression '*' unary-expression
		                              | multiplicative-expression '/' unary-expression
		                              | multiplicative-expression '%' unary-expression
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			self._binary_op(p)
	
	def p_additive_expression(self, p):
		''' additive-expression : multiplicative-expression
		                        | additive-expression '+' multiplicative-expression
		                        | additive-expression '-' multiplicative-expression 
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			self._binary_op(p)
	
	def p_shift_expression(self, p):
		''' shift-expression : additive-expression
		                     | shift-expression SHL additive-expression
		                     | shift-expression SHR additive-expression   
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			self._binary_op(p)
	
	def p_relational_expression(self, p):
		''' relational-expression : shift-expression
		                          | relational-expression '<' shift-expression
		                          | relational-expression '>' shift-expression
		                          | relational-expression LTE shift-expression
		                          | relational-expression GTE shift-expression
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			self._binary_op(p)
	
	def p_equality_expression(self, p):
		''' equality-expression : relational-expression
		                        | equality-expression EQ relational-expression
		                        | equality-expression NE relational-expression
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			self._binary_op(p)
	
	def p_and_expression(self, p):
		''' and-expression : equality-expression
		                   | and-expression '&' equality-expression
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			self._binary_op(p)
	
	def p_xor_expression(self, p):
		''' xor-expression : and-expression
		                   | xor-expression '^' and-expression 
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			self._binary_op(p)
	
	def p_or_expression(self, p):
		''' or-expression : xor-expression
		                  | or-expression '|' xor-expression 
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			self._binary_op(p)
	
	def p_and_test(self, p):
		''' and-test : or-expression
		             | and-test AND or-expression
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			p[0] = Node('and_test', [p[1], p[3]])
	
	# TODO: test this right recursion
	def p_or_test(self, p):
		''' or-test : and-test
		            | and-test OR or-test
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			p[0] = Node('or_test', [p[1], p[3]])
	
	def p_conditional_expression(self, p):
		''' conditional-expression : or-test
		                           | or-test '?' expression ':' assignment-expression
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			p[0] = Node('ternary', (p[1], p[3], [5]))
	
	# TODO: test this right recursion
	def p_assignment_expression(self, p):
		''' assignment-expression : conditional-expression
		                          | or-test assignment-operator assignment-expression
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			p[0] = Assign(p[1], p[2], p[3])
			p[0].ret_type = getattr(p[3], 'ret_type', type(p[3]))
	
	def p_assignment_operator(self, p):
		''' assignment-operator : '='
		                        | MULEQ
		                        | DIVEQ
		                        | MODEQ
		                        | ADDEQ
		                        | SUBEQ
		                        | ANDEQ
		                        | XOREQ
		                        | OREQ
		                        | SHLEQ
		                        | SHREQ
		'''
		p[0] = p[1]
	
	def p_expression(self, p):
		''' expression : assignment-expression
		           | expression ',' assignment-expression
		'''
		if len(p) == 2:
			p[0] = p[1]
		else:
			if isinstance(p[1], (tuple, list)):
				p[0] = list(p[1]) + [p[3]]
			else:
				p[0] = [p[1], p[3]]
	
	def p_conditional_expr_list(self, p):
		''' conditional-expr-list : conditional-expression
		                          | conditional-expr-list ',' conditional-expression
		'''
