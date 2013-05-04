import sys

from kaml.lexer import Lexer

if __name__ == '__main__':
	args = sys.argv
	if len(args) >= 2:
		file_name = args[1]
		
		l = Lexer()
		with open(file_name) as fp:
			for t in l.tokenize(unicode(fp.read())):
				print t
