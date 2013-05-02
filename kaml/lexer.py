from ply import lex
# Influence from pycparser, and aptana's CSS.bnf

class Lexer(object):
	tokens = list("'\"=.,/[]{}|\\!$%^&*()-=+?:;<>")
	
	def __init__(self, **kwargs):
		self.lexer = lex.lex(module = self, **kwargs)
	
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
	
	t_LTE = r'<='
	t_GTE = r'>='
	t_EQ = r'=='
	t_NE = r'!='
	t_AND = r'&&'
	t_OR = r'\|\|'
	t_SHL = r'<<'
	t_SHR = r'>>'
	t_ADDEQ = r'\+='
	t_SUBEQ = r'\-='
	t_MULEQ = r'\*='
	t_DIVEQ = r'/='
	t_MODEQ = r'%='
	t_SHLEQ = r'<<='
	t_SHREQ = r'>>='
	t_ANDEQ = r'&='
	t_XOREQ = r'^='
	t_OREQ = r'\|='
	
	t_WS = r'[\t ]'
	
	
	states = (
		('string_sg', 'inclusive'),
		('string_dbl', 'inclusive'),
		('variable_string', 'inclusive'),
	)
	
	def t_NL(self, t):
		r'\n+'
		t.lexer.lineno += len(t.value)
	
	def t_ID(self, t):
		r'\-?[a-zA-Z_\-][a-zA-Z_0-9\-]*'
		if t.value in self.reserved:
			t.type = self.reserved[t.value]
		return t
	
	def t_INT_LIT(self, t):
		r'[1-9][0-9]*'
		t.value = int(t.value)
		return t
	
	def t_FLOAT_LIT(self, t):
		r'[0-9]+\.[0-9]+'
		t.value = float(t.value)
		return t
	
	def t_STRING_BEGIN(self, t):
		r'[\'"]'
		if t.value == "'":
			self.lexer.push_state('string_sg')
		elif t.value == '"':
			self.lexer.push_state('string_dbl')
		
	# Strings =====
	rx_nonascii = r'[^\0-\177]'
	rx_unicode = r'\\[0-9a-fA-F]{1, 6}(\r\n | [ \n\r\t\f])?'
	rx_escape = r'{} | \\[^\n\r\f0-9a-fA-F]'.format(rx_unicode)
	rx_n1 = r'\n |\r\n |\r |\f'
	rx_string_dbl = r'([^\n\r\f\\"]|\\{} | {})*'.format(rx_n1, rx_escape)
	rx_string_sg = r'([^\n\r\f\\\']|\\{} | {})*'.format(rx_n1, rx_escape)
	
	
	def t_string_sg_SIMPLE_VAR(self, t):
		r = '\$'
	
	# End Strings ====
