import argparse
from pprint import pprint
import sys

from kaml.parser import Parser
from kaml.lexer import Lexer

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--trace', action = 'store_true')
parser.add_argument('input_file', metavar = 'INPUT_FILE', type = str)
parser.add_argument('-l', '--lexeronly', action = 'store_true')

if __name__ == '__main__':
	argv = sys.argv
	if len(argv) >= 2:
		args = parser.parse_args(argv[1:])
		
		with open(args.input_file) as fp:
			if args.lexeronly:
				l = Lexer(trace = args.trace)
				for t in l.tokenize(unicode(fp.read())):
					print t
			else:
				p = Parser(debug = True, write_tables = 0)
				
				ast = p.parse(fp.read(), debug = args.trace)
				
				if ast in (None, []):
					ast = '<empty tree>'
				
				pprint(ast)
				print('')
