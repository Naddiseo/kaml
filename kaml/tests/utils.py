from __future__ import unicode_literals

from ..lexer import T

def R(s):
	""" For writing raw strings """
	return '{}{}{}'.format('{{{', s, '}}}')

# ------ Token Shortcuts ---------
def S(s):
	return ('STRING_LIT', str(s))

def N(n, base = 10):
	return ('INT_LIT', int(str(n), base))

def F(f):
	return ('FLOAT_LIT', float(f))

def I(_id):
	return ('ID', _id)

def K(kw):
	return (kw.upper(), '-{}'.format(kw.lower()))

def L(_l):
	return (_l, _l)
# -------------------------------
