from __future__ import unicode_literals

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

def R(s):
	""" For writing raw strings """
	return '{}{}{}'.format('{{{', s, '}}}')

# ------ Token Shortcuts ---------
def S(s):
	return ('STRING_LIT', s)

def N(n):
	return ('INT_LIT', n)

def F(f):
	return ('FLOAT_LIT', f)

def I(_id):
	return ('ID', _id)

def K(kw):
	return (kw, '-{}'.format(kw.lower()))

def W(_w = None):
	#return ('WS', _w)
	return None

def L(_l):
	return (_l, _l)
# -------------------------------
