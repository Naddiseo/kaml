from __future__ import unicode_literals
import unittest


from kaml import Lexer
from .utils import R, S, I, T, N

class TestLexer(unittest.TestCase):
	
	def setUp(self):
		self.l = Lexer()
	
	def assertTokens(self, code, tokens = [], msg = None):
		lexer_tokens = [T(t.type, t.value) for t in list(self.l.tokenize(code)) if t]
		test_tokens = [T(*t) if isinstance(t, (list, tuple)) else t for t in tokens if t]
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
		code = "-def -set -for -if -elif -else -use -while -continue -break or and true false"
		tokens = [T(t.replace('-', '').upper()) for t in code.split()]
		
		self.assertTokens(code, tokens)
	
	def test_idents(self):
		self.assertTokens(
			"simplevar simple_var2 simple-var -simplevar -simple-var",
			[I('simplevar'), I('simple_var2'), I('simple-var'), I('-simplevar'), I('-simple-var')],
		)
		
		self.assertTokens('0-ident', [N('0'), I('-ident')])
		self.assertTokens('ident-0-ent', [I('ident-0-ent')])
	
	def test_numbers(self):
		pass
	
	def test_stringsg(self):
		tokens = [S('ABCD')]
		
		self.assertTokens("'ABCD'", tokens)
		
		# Concatenation
		self.assertTokens("'AB''CD'", tokens)
		
		# Concatenation with whitespace
		self.assertTokens("\n'AB'\n 'CD'\n", tokens)
		self.assertTokens(" \n 'AB' \n 'CD' \n ", tokens)
		
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
		self.assertTokens('\n "AB"\n "CD"\n ', tokens)
		self.assertTokens(' \n "AB" \n "CD" \n ', tokens)
		# Test escaped quote
		self.assertTokens(r"'\''", [S("'")])
		# escaped braces
		self.assertTokens(r'"{{"', [S("{")])
		self.assertTokens(r'"}}"', [S("}")])
	
	def test_string(self):
		
		# Mixed strings
		self.assertTokens(''' \n "AB" \n 'CD' \n ''', [ S('ABCD'), ])
		self.assertTokens(''' \n 'AB' \n "CD" \n ''', [S('ABCD'), ])
		self.assertTokens(''' \n {} \n "CD" \n 'EF' \n '''.format(R('AB')), [S('ABCDEF')])
		self.assertTokens(''' \n {} \n 'CD' \n "EF" \n '''.format(R('AB')), [S('ABCDEF')])
		self.assertTokens(''' \n "AB" \n {} \n 'EF' \n '''.format(R('CD')), [S('ABCDEF')])
		self.assertTokens(''' \n 'AB' \n {} \n "EF" \n '''.format(R('CD')), [S('ABCDEF')])
		self.assertTokens(''' \n "AB" \n 'CD' \n {} \n '''.format(R('EF')), [S('ABCDEF')])
		self.assertTokens(''' \n 'AB' \n "CD" \n {} \n '''.format(R('EF')), [S('ABCDEF')])
	
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
		self.assertTokens(''' "Hello " " {bar} World" ''', [S('Hello  '), I('bar'), S(' World')])
		self.assertTokens(''' "Hello " "{bar} World" ''', [S('Hello '), I('bar'), S(' World')])
		self.assertTokens('''"Hello {bar}"" World"''', [S('Hello '), I('bar'), S(' World')])
		self.assertTokens('''"Hello {bar}" " World"''', [S('Hello '), I('bar'), S(' World')])
		self.assertTokens('''"Hello {bar} ""World"''', [S('Hello '), I('bar'), S(' World')])
		self.assertTokens('''"Hello {bar} " "World"''', [S('Hello '), I('bar'), S(' World')])
		
		self.assertTokens('''" Hello {\nbar\n} World"''', [S(' Hello '), I('bar'), S(' World')])
		
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
	
	def test_rawstr(self):
		
		self.assertTokens(R(''), [S('')])
		self.assertTokens(R(' \n '), [S(' \n ')])
		self.assertTokens(R('"'), [S('"')])
		self.assertTokens(R("'"), [S('\'')])
		self.assertTokens(R("$"), [S('$')])
		# Escaping
		self.assertTokens(R(' \\n '), [S(' \\n ')])
		self.assertTokens(R('${{'), [S('${')])
		# Braces are just plain
		self.assertTokens(R("{"), [S('{')])
		self.assertTokens(R("{{"), [S('{{')])
		self.assertTokens(R("{{{{"), [S('{{{{')])
		
		# Interpolation is done with  ${}
		self.assertTokens(R("${hello}"), [S(''), I('hello'), S('')])
		self.assertTokens(R(" \n ${ \n Hello \n } \n "), [S(' \n '), I('Hello'), S(' \n ')])
		
		# Interpolation at the beginning and end of a raw string
		self.assertTokens(R("Hello ${foo}"), [S('Hello '), I('foo'), S('')])
		self.assertTokens(R("${foo} Hello "), [S(''), I('foo'), S(' Hello ')])
		self.assertTokens(R("${foo} Hello ${foo}"), [S(''), I('foo'), S(' Hello '), I('foo'), S('')])
