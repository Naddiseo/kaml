from ply import lex, yacc
# Influence from pycparser, and aptana's CSS.bnf

class Lexer(object):
	
	def __init__(self, **kwargs):
		self.lexer = lex.lex(module = self, **kwargs)
		
		self.nesting = 0
		
	def tokenize(self, data):
		self.lexer.input(data)
		while True:
			tok = self.lexer.token()
			if tok:
				yield tok
			else:
				break
	
	def find_tok_column(self, token):
		last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
		return token.lexpos - last_cr
	
	def _make_tok_location(self, token):
		return (token.lineno, self.find_tok_column(token))
	
	reserved = {k.strip() : k.strip().replace('-', '').upper() for k in """
	-fn -set -for -if -elif -else -use -while -continue -break
	or and true false 
	""".split()}
	
	reserved_words = reserved.values()
	other_symbols = [
		'ID',
		# Literals
		'INT_LIT', 'FLOAT_LIT', 'STRING_LIT',
		
		# Operators
		'ADDEQ', 'SUBEQ', 'MULEQ', 'DIVEQ', 'MODEQ',
		'ANDEQ', 'XOREQ', 'OREQ',
		'SHL', 'SHR', 'SHLEQ', 'SHREQ',
		'GTE', 'LTE', 'EQ', 'NE', 'GT', 'LT',
		
		# Separater
		'WS'
	]
	
	literals = [
		'+', '-',
		'*', '/', '%',
		'=', '>', '<',
		'~', '!', '^', '&', '|',
		'(', ')', '{', '}', '[', ']',
		'.', '?', ':', ';', ',',
		'#', '$',
	]
	tokens = reserved_words + other_symbols 
	
	t_INITIAL_variablestring_LTE = r'<='
	t_INITIAL_variablestring_GTE = r'>='
	t_INITIAL_variablestring_EQ = r'=='
	t_INITIAL_variablestring_NE = r'!='
	t_INITIAL_variablestring_AND = r'&&'
	t_INITIAL_variablestring_OR = r'\|\|'
	t_INITIAL_variablestring_SHL = r'<<'
	t_INITIAL_variablestring_SHR = r'>>'
	t_INITIAL_variablestring_ADDEQ = r'\+='
	t_INITIAL_variablestring_SUBEQ = r'\-='
	t_INITIAL_variablestring_MULEQ = r'\*='
	t_INITIAL_variablestring_DIVEQ = r'/='
	t_INITIAL_variablestring_MODEQ = r'%='
	t_INITIAL_variablestring_SHLEQ = r'<<='
	t_INITIAL_variablestring_SHREQ = r'>>='
	t_INITIAL_variablestring_ANDEQ = r'&='
	t_INITIAL_variablestring_XOREQ = r'^='
	t_INITIAL_variablestring_OREQ = r'\|='
	
	t_INITIAL_variablestring_WS = r'[\t ]'
	
	
	states = (
		('stringsg', 'exclusive'),
		('stringdbl', 'exclusive'),
		('variablestring', 'exclusive'),
	)
	
	def t_ANY_NL(self, t):
		r'\n+'
		t.lexer.lineno += len(t.value)
		t.type = 'WS'
		return t
	
	def t_INITIAL_variablestring_ID(self, t):
		r'[a-zA-Z_\-][a-zA-Z_0-9\-]*'
		if t.value in self.reserved:
			t.type = self.reserved[t.value]
		return t
	
	def t_INITIAL_variablestring_INT_LIT(self, t):
		r'[1-9][0-9]*'
		t.value = int(t.value)
		return t
	
	def t_INITIAL_variablestring_FLOAT_LIT(self, t):
		r'[0-9]+\.[0-9]+'
		t.value = float(t.value)
		return t
	
	def t_INITIAL_variablestring_STRING_BEGIN(self, t):
		r'[\'"]'
		if t.value == "'":
			print("Starting SG")
			self.lexer.push_state('stringsg')
		elif t.value == '"':
			print("Starting DBL")
			self.lexer.push_state('stringdbl')
		
	# Strings =====
	rx_nonascii = r'[^\0-\177]'
	rx_unicode = r'\\[0-9a-fA-F]{1, 6}(\r\n | [ \n\r\t\f])?'
	rx_escape = r'{} | \\[^\n\r\f0-9a-fA-F]'.format(rx_unicode)
	rx_n1 = r'\n |\r\n |\r |\f'
	rx_string_dbl = r'([^\n\r\f\\"]|\\{} | {})*'.format(rx_n1, rx_escape)
	rx_string_sg = r'([^\n\r\f\\\']|\\{} | {})*'.format(rx_n1, rx_escape)
	
	
	def t_stringsg_stringdbl_SIMPLE_VAR(self, t):
		r'\$[a-zA-Z_\-][a-zA-Z_0-9\-]*'
		t.type = 'ID'
		print("Simple var :".format(t.value))
		return t
	
	
	def t_stringsg_stringdbl_VAR_STRING_START(self, t):
		r'\{(?!\{)'
		print("Starting VARSTRING")
		self.nesting += 1
		self.lexer.push_state('variablestring')
	
	def t_stringsg_STRING_END_Q(self, t):
		r'\''
		print("Ending SG")
		self.lexer.pop_state()
		
	def t_stringdbl_STRING_END_Q(self, t):
		r'"'
		print("Ending DBL")
		self.lexer.pop_state()
	
	def t_stringsg_stringdbl_INNER(self, t):
		r'[^\{]+'
		t.type = 'STRING_LIT'
		return t
	
#	def t_stringsg_stringdbl_STRING_END(self, t):
#		r'\}(?!\{)'
#		print("Ending ")
#		self.lexer.pop_state()
#	

	def t_variablestring_LBRACE(self, t):
		r'\{'
		self.nesting += 1
		t.type = '{'
		return t
	
	def t_variablestring_END(self, t):
		r'\}'
		
		self.nesting -= 1
		print("nesting={}".format(self.nesting))
		if self.nesting == 0:
			print("Ending VARSTR")
			self.lexer.pop_state()
	
#	def t_variablestring_START(self, t):
#		r'.'
#		t.type = 'STRING_LIT'
#		return t
	
	
	
	# End Strings ====
