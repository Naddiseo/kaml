import sys

from kaml.lexer import Lexer

if __name__ == '__main__':
	args = sys.argv
	print args
	if len(args) >= 2:
		file_name = args[1]
		
		l = Lexer()
		with open(file_name) as fp:
			for t in l.tokenize(fp.read()):
				print t
