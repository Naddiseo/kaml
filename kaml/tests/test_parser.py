from __future__ import unicode_literals
import sys
import unittest

if sys.version_info[0] == 3:
	string_types = str
else:
	string_types = basestring

from ..astnodes import (
	TranslationUnit, FuncDef, FuncDecl, Suite, ReturnStmt, UseStmt,
	VariableDecl, NumberLiteral, StringLiteral, ParamSeq
)
from ..parser import Parser, ParseException

class TestParser(unittest.TestCase):
	def setUp(self):
		self.p = Parser()
	
	def _get_stmt_code(self, code):
		return 'def fn(){{ {code } }}'.format(code)
	
	def _get_expr_code(self, code):
		return 'def fn(){{ return {code}; }}'.format(code)
	
	def _get_stmt_tree(self, tree = None, *args):
		return TranslationUnit(
			FuncDef(
				FuncDecl('fn', ParamSeq(*args)),
				Suite(tree) if tree is not None else Suite()
			)
		)
	
	def assertParses(self, code, msg = None):
		self.assertNotIn(self.p.parse(code), (None, []), msg)
	
	def assertNotParses(self, code, msg = None):
		with self.assertRaises(ParseException):
			self.p.parse(code)
	
	def assertTree(self, ast, tree = [], msg = None):
		if isinstance(ast, string_types):
			ast = self.p.parse(ast)
		
		self.assertEqual(tree, ast, msg)
	
	def assertStmtTree(self, code, tree, msg = None):
		ast = self.p.parse(self._get_stmt_code(code))
		tree = self._get_stmt_tree(tree)
		self.assertTree(ast, tree, msg)
	
	def assertExprTree(self, code, tree, msg = None):
		ast = self.p.parse(self._get_expr_code(code))
		tree = self._get_stmt_tree(ReturnStmt(tree))
		self.assertTree(ast, tree, msg)
	
	def assertStmts(self, code, msg = None):
		self.assertParses(self._get_stmt_code(code), msg)
	
	def test_empty(self):
		self.assertParses('\n   \t')
	
	def test_comment(self):
		self.assertParses('// One line Comment\n  ')
		self.assertParses('// Line 1\n//Line 2')
		self.assertParses('/* multi\nline\ncomment*/')
		self.assertParses('-def /*inline comment */ fn(){}')
	
	def test_use(self):
		self.assertTree('-use foo;', TranslationUnit(UseStmt('foo', '')))
		self.assertTree('-use foo.bar;', TranslationUnit(UseStmt('foo', 'bar')))
		self.assertTree('-use foo.bar.baz;', TranslationUnit(UseStmt(UseStmt('foo', 'bar'), 'baz')))
		self.assertTree('-use foo.*;', TranslationUnit(UseStmt('foo', '*')))
		
		self.assertTree('-use foo;-use bar;', TranslationUnit(UseStmt('foo', ''), UseStmt('bar', '')))
		
		self.assertNotParses('-use *;')
		self.assertParses('-use -foo.-bar;')
	
	def test_function_def(self):
		self.assertTree('-def fn(){}', self._get_stmt_tree(None))
		self.assertTree('-def fn(arg1){}', self._get_stmt_tree(None, VariableDecl('arg1', [])))
		self.assertTree('-def fn(arg1,){}', self._get_stmt_tree(None, VariableDecl('arg1', [])))
		self.assertTree('-def fn(arg1, arg2){}',
			self._get_stmt_tree(None,
				VariableDecl('arg1', []),
				VariableDecl('arg2', [])
			)
		)
		self.assertTree('-def fn(arg1, arg2,){}',
			self._get_stmt_tree(None,
				VariableDecl('arg1', []),
				VariableDecl('arg2', [])
			)
		)
		self.assertTree('-def fn(arg1=0, arg2){}',
			self._get_stmt_tree(None,
				VariableDecl('arg1', NumberLiteral(0)),
				VariableDecl('arg2', [])
			)
		)
		self.assertTree('-def fn(arg1, arg2=0){}',
			self._get_stmt_tree(None,
				VariableDecl('arg1', []),
				VariableDecl('arg2', NumberLiteral(0))
			)
		)
		self.assertTree('-def fn(arg1=0, arg2,){}',
			self._get_stmt_tree(None,
				VariableDecl('arg1', NumberLiteral(0)),
				VariableDecl('arg2', [])
			)
		)
		self.assertTree('-def fn(arg1, arg2=0,){}',
			self._get_stmt_tree(None,
				VariableDecl('arg1', []),
				VariableDecl('arg2', NumberLiteral(0))
			)
		)
		self.assertTree('-def fn(arg1=1, arg2=0){}',
			self._get_stmt_tree(None,
				VariableDecl('arg1', NumberLiteral(1)),
				VariableDecl('arg2', NumberLiteral(0))
			)
		)
		self.assertTree('-def fn(arg1=1, arg2=0,){}',
			self._get_stmt_tree(None,
				VariableDecl('arg1', NumberLiteral(1)),
				VariableDecl('arg2', NumberLiteral(0))
			)
		)
		self.assertTree('-def fn(arg1="1", arg2="0"){}',
			self._get_stmt_tree(None,
				VariableDecl('arg1', StringLiteral("1")),
				VariableDecl('arg2', StringLiteral("0"))
			)
		)
		

if __name__ == '__main__':
	unittest.main()
