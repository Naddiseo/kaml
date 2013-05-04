from __future__ import unicode_literals
import re, sys

from ply import lex
# Influence from pycparser, and aptana's CSS.bnf

class Lexer(object):
	
	def __init__(self, **kwargs):
		self.log = lex.PlyLogger(sys.stderr)
		self.lexer = lex.lex(module = self, reflags = re.U, debuglog = self.log, **kwargs)
		self.lexer.lextokens['{'] = 1
		self.lexer.lextokens['}'] = 1
		self.nesting = 0
		self.rnesting = 0 # for raw strings
		
	def tokenize(self, data):
		self.lexer.input(data)
		while True:
			tok = self.lexer.token()
				
			if tok:
				value = ''
				lineno = tok.lineno
				lexpos = tok.lexpos
				while tok and tok.type == 'STRING_LIT':
					value += tok.value
					tok = self.lexer.token()
					while tok and tok.type in ('WS', 'NL'):
						tok = self.lexer.token()
				else:
					if len(value) > 0:
						tok = lex.LexToken()
						tok.type = 'STRING_LIT'
						tok.value = value
						tok.lineno = lineno
						tok.lexpos = lexpos
				yield tok
			else:
				break
	
	def find_tok_column(self, token):
		last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
		return token.lexpos - last_cr
	
	def _make_tok_location(self, token):
		return (token.lineno, self.find_tok_column(token))
	
	def push(self, s):
		t = '-' * len(self.lexer.lexstatestack)
		self.log.debug("{}Starting {}".format(t, s))
		self.lexer.push_state(s)
	
	def pop(self):
		t = '-' * (len(self.lexer.lexstatestack) - 1)
		current = self.lexer.current_state()
		self.lexer.pop_state()
		following = self.lexer.current_state()
		self.log.debug("{}Ending {}. Continuing {}".format(t, current, following))
		
	
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
		'WS',
		
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
		('rawstr', 'exclusive'),
	)
	
	def t_error(self, t):
		print("Error")
	
	def t_stringsg_stringdbl_error(self, t):
		print("Error in String")
	
	def t_variablestring_error(self, t):
		print("Error in var string")
	
	def t_rawstr_error(self, t):
		print("Error in rawstr")
	
	def t_INITIAL_variablestring_NL(self, t):
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
			self.push('stringsg')
		elif t.value == '"':
			self.push('stringdbl')
	
	def t_INITIAL_variablestring_RAWBLOCK_BEGIN(self, t):
		r'\{\{'
		self.push('rawstr')
	
	# Variable interpolation
	def t_variablestring_LBRACE(self, t):
		r'\{'
		self.nesting += 1
		t.type = '{'
		return t
	
	def t_variablestring_END(self, t):
		r'\}'
		t.type = '}'
		
		self.nesting -= 1
		
		if self.nesting == 0:
			self.pop()
		
		if len(self.lexer.lexstatestack) > 1:
			if self.lexer.lexstatestack[-1] not in ('rawstr',):
				return t
		
		#return t
	# End Variable Interpolation ========
	def t_stringsg_stringdbl_rawstr_NL(self, t):
		r'\n+'
		self.lexer.lineno += len(t.value)
		t.type = 'STRING_LIT'
		return t
		
	def t_rawstr_INNER(self, t):
		r'[^\{\}]+'
		t.type = 'STRING_LIT'
		#self.log.debug('rawstr inner')
		return t
	
	
	def t_rawstr_INNER2(self, t):
		r'\}(?!\})'
		t.type = 'STRING_LIT'
		return t
	
	def t_rawstr_ESCAPED_BRACE(self, t):
		r'\{\{'
		self.rnesting += 1
		t.value = '{'
		t.type = 'STRING_LIT'
		#self.log.debug('Escaped brace "{"')
		return t
	
	def t_rawstr_END(self, t):
		r'\}\}'
		
		t.value = '}'
		t.type = 'STRING_LIT'
			
		if self.rnesting == 0:
			self.pop()
		else:
			self.rnesting -= 1
			#self.log.debug('Escaped brace "}"')
			return t
	# Raw String Blocks
	
	# String Literals =====
	
	def t_stringsg_stringdbl_rawstr_ESCAPE_CHAR(self, t):
		r'\\[0-9a-fA-F]{1, 6}(\r\n | [ \n\r\t\f])? | \\[^\n\r\f0-9a-fA-F]'
		t.type = 'STRING_LIT'
		self.lexer.lineno += t.value.count('\n')
		return t
		
	
	def t_stringsg_stringdbl_rawstr_SIMPLE_VAR(self, t):
		r'\$[a-zA-Z_\-][a-zA-Z_0-9\-]*'
		t.type = 'ID'
		self.log.debug("Simple var :".format(t.value))
		return t
	
	
	def t_stringsg_stringdbl_rawstr_VAR_STRING_START(self, t):
		r'\{(?!\{)'
		self.nesting += 1
		self.push('variablestring')
	
	def t_stringsg_STRING_END_Q(self, t):
		r'\''
		self.pop()
		
	def t_stringdbl_STRING_END_Q(self, t):
		r'"'
		self.pop()
	
	def t_stringsg_stringdbl_INNER(self, t):
		r'[^\{\'\"]+'
		t.type = 'STRING_LIT'
		self.log.debug('inner')
		return t
	# End Strings ====
