from __future__ import unicode_literals
import unittest

from ply.lex import LexToken

from kaml import Lexer
from twisted.trial.test.test_assertions import AssertTrueTests

class T(LexToken):
	__slots__ = ('type', 'value', 'lineno', 'lexpos')
	def __init__(self, t, v = None):
		if isinstance(t, (tuple, list)):
			l = len(t)
			self.type = t[0] if l else t
			self.value = t[1] if l > 1 else v
			self.lineno = t[2] if l > 2 else 0
			self.lexpos = t[3] if l > 3 else 0
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
			ret = ret and other_v == self.value
		
		return ret
	
	def __repr__(self):
		return "Token({}, {!r})".format(self.type, self.value)

def S(s):
	return ('STRING_LIT', s)

def N(n):
	return ('INT_LIT', n)

def I(_id):
	return ('ID', _id)

def K(kw):
	return (kw, '-{}'.format(kw.lower()))

def W(_w = None):
	return ('WS', _w)

class Test(unittest.TestCase):
	
	def setUp(self):
		self.l = Lexer()
	
	def assertTokens(self, code, tokens = [], filter_ws = False, msg = None):
		if filter_ws:
			lexer_tokens = [T(t.type, t.value) for t in list(self.l.tokenize(code)) if t.type != 'WS']
		else:
			lexer_tokens = [T(t.type, t.value) for t in list(self.l.tokenize(code))]
		test_tokens = [T(*t) if isinstance(t, (list, tuple)) else t for t in tokens]
		try:
			self.assertTokenLists(test_tokens, lexer_tokens, msg)
		except AssertionError:
			print "For code `{}`".format(code)
			raise
	
	def assertTokenLists(self, expected_tokens, actual_tokens, msg = None):
		self.l = Lexer() # Recreate in case a previous test leaves the lexer in a bad state
		try:
			self.assertEqual(len(expected_tokens), len(actual_tokens))
		except AssertionError:
			print("{}\n{}".format(expected_tokens, actual_tokens))
			raise
		
		for expected, actual in zip(expected_tokens, actual_tokens):
			self.assertEqual(expected, actual, msg)
	
	def test_kw_tokens(self):
		code = "-fn -set -for -if -elif -else -use -while -continue -break or and true false"
		tokens = [T(t.replace('-', '').upper()) for t in code.split()]
		
		self.assertTokens(code, tokens, filter_ws = True)
	
	def test_stringsg(self):
		tokens = [S('ABCD')]
		
		self.assertTokens("'ABCD'", tokens)
		
		# Concatenation
		self.assertTokens("'AB''CD'", tokens)
		
		# Concatenation with whitespace
		self.assertTokens("\n'AB'\n 'CD'\n", [W('\n')] + tokens + [W('\n')],)
		self.assertTokens(" \n 'AB' \n 'CD' \n ", [W(' \n ')] + tokens + [W(' \n ')])
		
		# Test escaped quote
		self.assertTokens(r'"\""', [S('"')])
		# Escaped brace
		self.assertTokens(r"'{{'", [S("{")])
		self.assertTokens(r"'}}'", [S("}")])
		
	def test_stringdbl(self):
		tokens = [S('ABCD')]
		
		self.assertTokens('"ABCD"', tokens)
		self.assertTokens('"AB\nCD"', [S('AB\nCD')])
		
		# Concatenation
		self.assertTokens('"AB""CD"', tokens)
		
		# Concatenation with whitespace
		self.assertTokens('\n "AB"\n "CD"\n ', [W('\n ')] + tokens + [W('\n ')])
		self.assertTokens(' \n "AB" \n "CD" \n ', [W(' \n ')] + tokens + [W(' \n ')])
		# Test escaped quote
		self.assertTokens(r"'\''", [S("'")])
		# escaped braces
		self.assertTokens(r'"{{"', [S("{")])
		self.assertTokens(r'"}}"', [S("}")])
	
	def test_string(self):
		
		# Mixed strings
		self.assertTokens(''' \n "AB" \n 'CD' \n ''', [W(' \n '), S('ABCD'), W(' \n ')])
		self.assertTokens(''' \n 'AB' \n "CD" \n ''', [W(' \n '), S('ABCD'), W(' \n ')])
	
	def test_simple_interpolation(self):
		# Simple var
		self.assertTokens("'$bar'", [S(''), I('$bar'), S('')])
		# Simple var embedded
		self.assertTokens("'Hello $bar World'", [S('Hello '), I('$bar'), S(' World')])
		
		# Simple in DBL
		self.assertTokens('"$bar"', [S(''), I('$bar'), S('')])
		#simple embedded in dbl
		self.assertTokens('"Hello $bar World"', [S('Hello '), I('$bar'), S(' World')])
		
		# Curly var
		self.assertTokens("'{bar}'", [S(''), I('bar'), S('')])
		self.assertTokens('"{bar}"', [S(''), I('bar'), S('')])
		self.assertTokens("'Hello {bar} World'", [S('Hello '), I('bar'), S(' World')])
		self.assertTokens('"Hello {bar} World"', [S('Hello '), I('bar'), S(' World')])
		
		# Interpolation with strings and whitespace
		self.assertTokens('''"Hello ""{bar} World"''', [S('Hello '), I('bar'), S(' World')])
		self.assertTokens(''' "Hello " " {bar} World" ''', [W(' '), S('Hello  '), I('bar'), S(' World'), W(' ')])
		self.assertTokens(''' "Hello " "{bar} World" ''', [W(' '), S('Hello '), I('bar'), S(' World'), W(' ')])
		self.assertTokens('''"Hello {bar}"" World"''', [S('Hello '), I('bar'), S(' World')])
		self.assertTokens('''"Hello {bar}" " World"''', [S('Hello '), I('bar'), S(' World')])
		self.assertTokens('''"Hello {bar} ""World"''', [S('Hello '), I('bar'), S(' World')])
		self.assertTokens('''"Hello {bar} " "World"''', [S('Hello '), I('bar'), S(' World')])
		
		# Dollar curly
		self.assertTokens("'${bar}'", [S(''), I('bar'), S('')])
		self.assertTokens('"${bar}"', [S(''), I('bar'), S('')])
		self.assertTokens("'Hello ${bar} World'", [S('Hello '), I('bar'), S(' World')])
		self.assertTokens('"Hello ${bar} World"', [S('Hello '), I('bar'), S(' World')])
		
		# Test escaped ${}
		self.assertTokens("'${{'", [S('${')])
		self.assertTokens('"${{"', [S('${')])
		self.assertTokens("'$'", [S('$')])
		self.assertTokens('"$"', [S('$')])
		self.assertTokens("'$ '", [S('$ ')])
		self.assertTokens('"$ "', [S('$ ')])
	
	def test_concat_white(self):
		""" Tests the WS token concatenation in the lexer """
		
		tokens1 = map(T, [('WS', ' '), ('WS', ' '), ('WS', ' ')])
		expected = map(T, [('WS', '   ')])
		
		actual = self.l._concat_ws_tokens(tokens1, 0)
		
		self.assertTokenLists(expected, actual)
	
	def test_rawstr(self):
		self.assertTokens('''{{}}''', [S('')])
		self.assertTokens('''{{ \n }}''', [S(' \n ')])
		self.assertTokens('''{{"}}''', [S('"')])
		self.assertTokens('''{{'}}''', [S('\'')])
		self.assertTokens('''{{$}}''', [S('$')])
		self.assertTokens('''{{{}}''', [S('{')])
		self.assertTokens('''{{{{}}''', [S('{{')])
		
if __name__ == '__main__':
	unittest.main()
