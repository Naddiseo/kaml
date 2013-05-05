import argparse
from pprint import pprint
import sys

from kaml.parser import Parser

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--trace', action = 'store_true')
parser.add_argument('input_file', metavar = 'INPUT_FILE', type = str)

if __name__ == '__main__':
	argv = sys.argv
	if len(argv) >= 2:
		args = parser.parse_args(argv[1:])
		
		#l = Lexer(trace = args.trace)
		#with open(args.input_file) as fp:
		#	for t in l.tokenize(unicode(fp.read())):
		#		print t
		
		p = Parser(debug = True)
		
		with open(args.input_file) as fp:
			ast = p.parse(fp.read(), debug = 0)
			
			if ast in (None, []):
				ast = '<empty tree>'
			
			pprint(ast)
			print('')
