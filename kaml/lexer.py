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
		self.rnesting = 0# for raw strings
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
					for t in self._tokenize_string(tok):
						yield t
					
				elif tok.type == 'WS':
					# Whitespace can also concatenate
					ws_tok = lex.LexToken()
					ws_tok.type = 'WS'
					ws_tok.lineno = tok.lineno
					ws_tok.lexpos = tok.lexpos
					ws_tok.value = ''
					while tok and tok.type == 'WS':
						ws_tok.value += tok.value
						tok = self._get_token()
					
					yield ws_tok
					self._push_token(tok)
				else:
					yield tok
			else:
				break
	
	def _tokenize_string(self, tok):
		
		# String literals concatenate when next to each other
		if tok.type in 'STRING_LIT':
			stack = []
			# Any whitespace between string_literals can be forgotten
			while tok and tok.type in ('STRING_LIT', 'WS'):
				stack.append(tok)
				tok = self._get_token()
			
			if len(stack):
				# Since `stack` is only strings and WS, we can divide it into
				# three sections:
				#  1 - Initial Whitespace
				#  2 - Final Whitespace
				#  3 - All tokens inbetween
				# The initial and final whitespace can be concatenated into
				# just one or zero whitespace tokens on each end
				# then all whitespace in the middle can be dropped, and then
				# all strings concatenated
				
				# Step 1: Concatenate initial whitespace
				stack = self._concat_ws_tokens(stack, 0)
				
				# Step 2: Concatenate final whitespace
				if stack[-1].type == 'WS':
					offset = len(stack) - 1
					for i in reversed(xrange(0, len(stack))):
						if stack[i].type == 'STRING_LIT':
							offset = i + 1
							break
					stack = self._concat_ws_tokens(stack, offset)
				
				# At this point, there should only be an optional WS token
				# at the beginning and end
				l = len(stack)
				
				if l > 1:
					start = 0
					end = l
					if stack[0].type == 'WS':
						start = 1
					if stack[-1].type == 'WS':
						end = l - 1
					
					s_tok = lex.LexToken()
					s_tok.type = 'STRING_LIT'
					s_tok.value = ''
					s_tok.lineno = stack[start].lineno
					s_tok.lexpos = stack[start].lexpos
					
					last_tok = None
					
					for i in xrange(start, end):
						last_tok = stack[i]
						if last_tok.type == 'STRING_LIT':
							s_tok.value += last_tok.value
					
					assert last_tok.type == 'STRING_LIT'
					stack_begin = stack[:start]
					stack_end = stack[end :]
					stack = stack_begin + [s_tok] + stack_end
				# Now yield the modified stack
				for t in stack:
					yield t
		
		if tok:
			yield tok
	
	def _concat_ws_tokens(self, tokens, offset):
		start_offset = offset
		tok = tokens[offset]
		l = len(tokens)
		
		if tok.type == 'WS':
			value = ''
			while tok and tok.type == 'WS':
				value += tok.value
				offset += 1
				if offset < l:
					tok = tokens[offset]
				else:
					break
			
			tok = lex.LexToken()
			tok.type = 'WS'
			tok.value = value
			tok.lineno = tokens[start_offset].lineno
			tok.lexpos = tokens[start_offset].lexpos
			
			tokens_start = tokens[:start_offset]
			tokens_end = tokens[offset:]
			tokens = tokens_start + [tok] + tokens_end
				
		return tokens
	
	def find_tok_column(self, token):
		last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
		return token.lexpos - last_cr
	
	def _make_tok_location(self, token):
		return (token.lineno, self.find_tok_column(token))
	
	def push(self, s):
		t = '-' * len(self.lexer.lexstatestack) #@UnusedVariable
		#self.log.debug("{}Starting {}".format(t, s))
		self.lexer.push_state(s)
	
	def pop(self):
		t = '-' * (len(self.lexer.lexstatestack) - 1) #@UnusedVariable
		current = self.lexer.current_state() #@UnusedVariable
		self.lexer.pop_state()
		following = self.lexer.current_state() #@UnusedVariable
		#self.log.debug("{}Ending {}. Continuing {}".format(t, current, following))
		
	
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
		t.value = t.value[1:] # Remove the slash
		self.lexer.lineno += t.value.count('\n')
		return t
		
	
	def t_stringsg_stringdbl_rawstr_SIMPLE_VAR(self, t):
		r'\$[a-zA-Z_\-][a-zA-Z_0-9\-]*'
		t.type = 'ID'
		#self.log.debug("Simple var :".format(t.value))
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
		r'[^\{\'\"\$]+'
		t.type = 'STRING_LIT'
		#self.log.debug('inner')
		return t
	# End Strings ====
