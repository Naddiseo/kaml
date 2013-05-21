import argparse
from pprint import pprint
import sys, os

from kaml.recdec import Parser
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
				for t in Lexer(data = unicode(fp.read())):
					print t
			else:
				base_path = os.path.abspath(os.path.dirname(__file__))
				lib_path = os.path.join(base_path, 'kaml', 'lib')
				p = Parser(debug = True, write_tables = 0, search_paths = [lib_path])
				
				ast = p.parse(fp.read(), debug = args.trace)
				
				if ast in (None, []):
					ast = '<empty tree>'
				print ast.eval(ast.scope)
				pprint(ast)
				print('')
