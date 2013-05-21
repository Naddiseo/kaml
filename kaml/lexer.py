from __future__ import unicode_literals
import re, sys

from ply import lex
from ply.lex import LexToken

class T(LexToken):
	__slots__ = ('type', 'value', 'lineno', 'lexpos')
	def __init__(self, t, v = None):
		if isinstance(t, (tuple, list)):
			l = len(t)
			self.type = t[0] if l else t
			self.value = t[1] if l > 1 else v
			self.lineno = t[2] if l > 2 else 0
			self.lexpos = t[3] if l > 3 else 0
		elif isinstance(t, LexToken):
			self.lineno = t.lineno
			self.lexpos = t.lexpos
			self.type = t.type
			self.value = t.value
		else:
			self.lineno = 0
			self.lexpos = 0
			self.type = t
			self.value = v
	
	def __eq__(self, other):
		other_t = None
		other_v = None
		
		if isinstance(other, (tuple, list)):
			if len(other) == 2:
				other_t, other_v = other
			elif len(other) == 1:
				other_t = other[0]
			else:
				return False
		
		elif isinstance(other, (T, LexToken)):
			other_t = other.type
			other_v = other.value
		
		else:
			return False
		
		ret = other_t == self.type
		
		if all([other_v is not None, self.value is not None]):
			fn = {
				'INT_LIT' : int,
				'FLOAT_LIT' : float,
			}
			
			self.value = fn.get(self.type, unicode)(self.value)
			other_v = fn.get(self.type, unicode)(other_v)
			
			ret = ret and other_v == self.value
		
		return ret
	
	def __repr__(self):
		return "Token({}, {!r})".format(self.type, self.value)

class LexerError(Exception): pass

class Lexer(object):
	
	def __init__(self, **kwargs):
		data = kwargs.pop('data', None)
		
		self.log = lex.PlyLogger(sys.stderr)
		self.lexer = lex.lex(module = self, reflags = re.U, debuglog = self.log, **kwargs)
		self.lexer.lextokens.update({
			'{' : 1, '}' : 1,
			'[' : 1, ']' : 1,
		})
		self.nesting = 0
		self.tok_stack = []
		
		if data is not None:
			self.lexer.input(data)
	
	def __get_token(self):
		''' Returns a raw token from either the stack, or a new token'''
		if len(self.tok_stack):
			return self.tok_stack.pop(0)
		
		return T(self.lexer.token())
	
	def __join_str(self):
		''' Concatenates adjacent string literals '''
		tok = self.__get_token()
		if tok and tok.type is not None:
			if tok.type == 'STRING_LIT':
				stack = [tok]
				
				# Add all WS and STRING_LIT tokens to a stack
				while True:
					t = self.__get_token()
					stack.append(t)
					if t.type not in ('WS', 'STRING_LIT'):
						break
				
				# Now join all STRING_LIT WS* STRING_LIT sequences
				
				## How many STRING_LIT tokens in the stack?
				sl = len(filter(lambda t: t.type == 'STRING_LIT', stack))
				
				if sl > 1:
					### Join the sequences
					#### Find the right most STRING_LIT
					r_index = next((i for i, x in enumerate(reversed(stack)) if x.type == 'STRING_LIT'), None)
					if r_index is None:
						raise LexerError("Could not find right STRING_LIT", stack)
					
					#### Since the list was reversed, undo.
					r_index = len(stack) - r_index
					i = r_index
					
					#### Join all tokens between 1 and r_index
					t = T(stack[0])
					t.value = ''.join((t.value for t in stack[:r_index] if t.type == 'STRING_LIT'))
					
				else:
					### Only the first one
					t = stack[0]
					i = 1
					
				# Now copy any extra tokens to tok_stack
				for tok in stack[i:]:
					self._push_token(tok)
				
				return t
		
		return tok
	
	def token(self, filter_ws = True):
		''' Public interface for getting a token, optionally strips WS'''
		t = self.__join_str()
		if filter_ws:
			while t.type == 'WS':
				t = self.__join_str()
		return t
	
	
	def _push_token(self, t):
		self.tok_stack.append(t)
	
	untoken = _push_token
		
	def set_data(self, data):
		self.lexer.input(unicode(data))
	
	def __iter__(self):
		while True:
			t = self.token()
			if not t or t.type is None:
				raise StopIteration
			yield t
	
	def la(self, n = 1, filter_ws = True):
		''' Look ahead n tokens 
			Makes sure there are at least N tokens on the stack
		'''
			
		if filter_ws:
			get_stack = lambda: filter(lambda t: t.type != 'WS', self.tok_stack)
		else:
			get_stack = lambda:self.tok_stack
		
		i = j = len(get_stack())
		while i < n:
			t = self.token()
			if t.type is None:
				return None
			self.tok_stack.insert(j, t)
			j = len(self.tok_stack)
			
			if filter_ws and t.type == 'WS':
				continue
			
			i += 1
			
		return get_stack()[n - 1]
	
	def skip(self, n):
		''' Skip the next n tokens '''
		for _ in xrange(n):
			self._get_token()
	
	def find_tok_column(self, token):
		last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
		return token.lexpos - last_cr
	
	def _make_tok_location(self, token):
		return (token.lineno, self.find_tok_column(token))
	
	def push(self, s):
		t = '-' * len(self.lexer.lexstatestack) #@UnusedVariable
#		if self.lexer.trace:
#			self.log.debug("{}Starting {}".format(t, s))
		self.lexer.push_state(s)
	
	def pop(self):
		t = '-' * (len(self.lexer.lexstatestack) - 1) #@UnusedVariable
		current = self.lexer.current_state() #@UnusedVariable
		self.lexer.pop_state()
		following = self.lexer.current_state() #@UnusedVariable
#		if self.lexer.trace:
#			self.log.debug("{}Ending {}. Continuing {}".format(t, current, following))
#		
	
	reserved = {k.strip() : k.strip().replace('-', '').upper() for k in """
	-def -set -for -if -elif -else -use -while -continue -break -return
	or and true false 
	""".split()}
	
	reserved_words = reserved.values()
	other_symbols = [
		'ID', 'SCOPEDID',
		# Literals
		'INT_LIT', 'FLOAT_LIT', 'STRING_LIT',
		
		# Operators
		'ADDEQ', 'SUBEQ', 'MULEQ', 'DIVEQ', 'MODEQ',
		'ANDEQ', 'XOREQ', 'OREQ',
		'SHL', 'SHR', 'SHLEQ', 'SHREQ',
		'GTE', 'LTE', 'EQ', 'NE',
		
		# WS
		'WS',
		
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
	#t_INITIAL_variablestring_PTR = r'\-\>'
	
	t_INITIAL_variablestring_WS = '[\t ]+'
	
	
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
		t.type = 'WS'
		return t
	
	def t_INITIAL_variablestring_ID(self, t):
		r'-?[a-zA-Z_][a-zA-Z_0-9\-]*'
		if t.value in self.reserved:
			t.type = self.reserved[t.value]
		return t
	
	def t_INITIAL_variablestring_FLOAT_LIT(self, t):
		r'[0-9]+\.[0-9]+'
		t.value = float(t.value)
		return t
	
	# Must come after FLOAT_LIT
	def t_INITIAL_variablestring_OCT_LIT(self, t):
		r'0[1-7]+'
		t.value = int(t.value, 8)
		t.type = 'INT_LIT'
		return t
	
	def t_INITIAL_variablestring_HEX_LIT(self, t):
		r'0x[0-9a-fA-F]+'
		t.value = int(t.value, 16)
		t.type = 'INT_LIT'
		return t
	
	# This must come after the OCT_LIT and HEX_LIT
	def t_INITIAL_variablestring_INT_LIT(self, t):
		r'(0|[1-9][0-9]*)'
		t.value = int(t.value)
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
