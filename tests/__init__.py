from __future__ import unicode_literals
import unittest

from ply.lex import LexToken

from kaml import Lexer

class T(LexToken):
	__slots__ = ('type', 'value', 'lineno', 'lexpos')
	def __init__(self, t, v = None):
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
			ret = ret and other_v == self.value
		
		return ret
	
	def __repr__(self):
		return "Token({}, {!r})".format(self.type, self.value)

def sl(s):
	return ('STRING_LIT', s)

def nl(n):
	return ('INT_LIT', n)

def name(_id):
	return ('ID', _id)

class Test(unittest.TestCase):
	
	def setUp(self):
		self.l = Lexer()
	
	def assertTokens(self, code, tokens = [], filter_ws = True, msg = None):
		lexer_tokens = [T(t.type, t.value) for t in list(self.l.tokenize(code)) if t.type != 'WS']
		test_tokens = []
		for t in tokens:
			test_tokens.append(T(*t) if isinstance(t, (list, tuple)) else t)
		
		try:
			self.assertEqual(len(lexer_tokens), len(test_tokens))
		except AssertionError:
			print("{}".format(lexer_tokens))
			raise
		
		for i in xrange(len(lexer_tokens)):
			t1 = lexer_tokens[i]
			t2 = test_tokens[i]
			
			self.assertEqual(t1, t2, msg)
	
	def test_kw_tokens(self):
		code = "-fn -set -for -if -elif -else -use -while -continue -break or and true false"
		tokens = [T(t.replace('-', '').upper()) for t in code.split()]
		
		self.assertTokens(code, tokens)
	
	def test_stringsg(self):
		code = "'ABCD'"
		tokens = [('STRING_LIT', 'ABCD')]
		
		self.assertTokens(code, tokens)
		
		# Concatenation
		code = "'AB''CD'"
		self.assertTokens(code, tokens)
		
		# Concatenation with whitespace
		code = "\n'AB'\n 'CD'\n"
		self.assertTokens(code, tokens)
	
	def test_stringdbl(self):
		code = '"ABCD"'
		tokens = [('STRING_LIT', 'ABCD')]
		
		self.assertTokens(code, tokens)
		
		# Concatenation
		code = '"AB""CD"'
		self.assertTokens(code, tokens)
		
		# Concatenation with whitespace
		code = '\n "AB"\n "CD"\n '
		self.assertTokens(code, tokens)
	
	def test_simple_interpolation(self):
		code = "'$bar'"
		tokens = [name('$bar')]
		
		self.assertTokens(code, tokens)
		
		code = "'Hello $bar World'"
		tokens = [sl('Hello '), name('$bar'), sl(' World')]
		
		self.assertTokens(code, tokens)

if __name__ == '__main__':
	unittest.main()
