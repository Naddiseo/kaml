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
		self.tok_stack = []
	
	def _get_token(self):
		if len(self.tok_stack):
			return self.tok_stack.pop(0)
		return self.lexer.token()
	
	def _push_token(self, t):
		self.tok_stack.append(t)
	
	def tokenize(self, data):
		self.lexer.input(unicode(data))
		while True:
			tok = self._get_token()
				
			if tok:
				if tok.type == 'STRING_LIT':
					t = lex.LexToken()
					t.lineno = tok.lineno
					t.type = 'STRING_LIT'
					t.lexpos = tok.lexpos
					t.value = ''
					
					while tok and tok.type == 'STRING_LIT':
						t.value += tok.value
						tok = self._get_token()
					
					yield t
				yield tok
			else:
				break
	
	def find_tok_column(self, token):
		last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
		return token.lexpos - last_cr
	
	def _make_tok_location(self, token):
		return (token.lineno, self.find_tok_column(token))
	
	def push(self, s):
		t = '-' * len(self.lexer.lexstatestack) #@UnusedVariable
		if self.lexer.trace:
			self.log.debug("{}Starting {}".format(t, s))
		self.lexer.push_state(s)
	
	def pop(self):
		t = '-' * (len(self.lexer.lexstatestack) - 1) #@UnusedVariable
		current = self.lexer.current_state() #@UnusedVariable
		self.lexer.pop_state()
		following = self.lexer.current_state() #@UnusedVariable
		if self.lexer.trace:
			self.log.debug("{}Ending {}. Continuing {}".format(t, current, following))
		
	
	reserved = {k.strip() : k.strip().replace('-', '').upper() for k in """
	-def -set -for -if -elif -else -use -while -continue -break -return
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
		'GTE', 'LTE', 'EQ', 'NE',
		
	]
	
	literals = [
		'+', '-',
		'*', '/', '%',
		'=', '>', '<',
		'~', '!', '^', '&', '|',
		'(', ')', '{', '}', '[', ']',
		'.', '?', ':', ';', ',',
		'#', '$', '\\',
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
	
	t_INITIAL_variablestring_ignore = '[\t ]'
	
	
	states = (
		('stringsg', 'exclusive'),
		('stringdbl', 'exclusive'),
		('variablestring', 'exclusive'),
		('rawstr', 'exclusive'),
		('comment', 'exclusive')
	)
	
	def t_error(self, t):
		print("Error")
	
	def t_stringsg_stringdbl_error(self, t):
		print("Error in String")
	
	def t_variablestring_error(self, t):
		print("Error in var string")
	
	def t_rawstr_error(self, t):
		print("Error in rawstr")
		
	def t_comment_error(self, t):
		print("Error in comment")
	
	def NL(self, t):
		r'\n+'
		t.lexer.lineno += len(t.value)
	
	def t_INITIAL_variablestring_SGCOMMENT(self, t):
		r'\/\/[^\n]*(\n|$)'
		t.lexer.lineno += 1
	
	def t_INITIAL_variablestring_MLCOMMENT(self, t):
		r'\/\*'
		self.push('comment')
	
	def t_INITIAL_variablestring_NL(self, t):
		r'\s*\n+\s*'
		t.lexer.lineno += len(t.value)
	
	def t_INITIAL_variablestring_ID(self, t):
		r'[a-zA-Z_\-][a-zA-Z_0-9\-]*'
		if t.value in self.reserved:
			t.type = self.reserved[t.value]
		return t
	
	def t_INITIAL_variablestring_INT_LIT(self, t):
		r'0|[1-9][0-9]*'
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
		# Push a dummy token
		t.value = ''
		t.type = 'STRING_LIT'
		return t
	
		
	def t_INITIAL_variablestring_RAWBLOCK_BEGIN(self, t):
		r'\{\{\{'
		self.push('rawstr')
		# Push a dummy token
		t.value = ''
		t.type = 'STRING_LIT'
		return t
	
	# Multiline Comments
	t_comment_ignore = r''
	
	def t_comment_END(self, t):
		r'(?<!\\)\*\/'
		self.pop()
	
	def t_comment_inner(self, t):
		r'[^\*]+'
		# Ignore
	
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
	t_rawstr_NL = NL
	t_rawstr_ignore = r''
	
	def t_rawstr_VAR_STRING_START2(self, t):
		r'\$\{(?!\{)'
		self.nesting += 1
		self.push('variablestring')
	
	def t_rawstr_INNER(self, t):
		r'[^\$\}]+'
		t.type = 'STRING_LIT'
		#self.log.debug('rawstr inner')
		return t
	
	def t_rawstr_dollar(self, t):
		r'\$((?!\{)|(\{\{))'
		t.type = 'STRING_LIT'
		
		if t.value == '${{':
			t.value = '${'
		
		return t
	
	def t_rawstr_INNER2(self, t):
		r'\}(?!\}\})'
		t.type = 'STRING_LIT'
		return t
	
	def t_rawstr_ESCAPED_BRACE(self, t):
		r'(?:{{)|(?:}}(?!\}))'
		#t.value = t.value[
		t.type = 'STRING_LIT'
		return t
	
	def t_rawstr_END(self, t):
		r'\}\}\}'
		t.value = ''
		
		t.type = 'STRING_LIT'
			
		self.pop()
		return t
	# Raw String Blocks
	
	# String Literals =====
	t_stringsg_stringdbl_NL = NL
	t_stringsg_stringdbl_ignore = r''
	
	def t_stringsg_stringdbl_ESCAPE_CHAR(self, t):
		r'\\[0-9a-fA-F]{1, 6}(\r\n | [ \n\r\t\f])? | \\[^\n\r\f0-9a-fA-F]'
		t.type = 'STRING_LIT'
		t.value = t.value[1:] # Remove the slash
		self.lexer.lineno += t.value.count('\n')
		return t
		
	def t_stringsg_stringdbl_SIMPLE_VAR(self, t):
		r'\$[a-zA-Z_\-][a-zA-Z_0-9\-]*'
		t.type = 'ID'
		#self.log.debug("Simple var :".format(t.value))
		return t
	
	def t_stringsg_stringdbl_VAR_STRING_START(self, t):
		r'\{(?!\{)'
		self.nesting += 1
		self.push('variablestring')
	
	def t_stringsg_stringdbl_VAR_STRING_START2(self, t):
		r'\$\{(?!\{)'
		self.nesting += 1
		self.push('variablestring')
	
	def t_stringsg_STRING_END_Q(self, t):
		r'\''
		self.pop()
		# Return a dummy string
		t.type = 'STRING_LIT'
		t.value = ''
		return t
		
	def t_stringdbl_STRING_END_Q(self, t):
		r'"'
		self.pop()
		# Return a dummy string
		t.type = 'STRING_LIT'
		t.value = ''
		return t
	
	def t_stringsg_stringdbl_INNER(self, t):
		r'[^\{\}\'\"\$]+'
		t.type = 'STRING_LIT'
		#self.log.debug('inner')
		return t
	
	def t_stringsg_stringdbl_ESCAPED_BRACES(self, t):
		r'(?:\{\{)|(?:\}\})'
		t.type = 'STRING_LIT'
		t.value = t.value[0]
		return t
	
	def t_stringsg_stringdbl_ESCAPED_DOLLAR(self, t):
		r'\$(?=[^a-zA-Z_\-])'
		t.type = 'STRING_LIT'
		return t
	
	# End Strings ====
