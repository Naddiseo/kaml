import argparse
import sys

from kaml.lexer import Lexer

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--trace', action = 'store_true')
parser.add_argument('input_file', metavar = 'INPUT_FILE', type = str)

if __name__ == '__main__':
	argv = sys.argv
	if len(argv) >= 2:
		args = parser.parse_args(argv[1:])
		
		l = Lexer(trace = args.trace)
		with open(args.input_file) as fp:
			for t in l.tokenize(unicode(fp.read())):
				print t
