from __future__ import unicode_literals
import unittest

from kaml.astnodes import * #@UnusedWildImport
from kaml.parser import Parser, ParseException

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
				FuncDecl('fn', list(*args)),
				Suite(tree) if tree is not None else Suite()
			)
		)
	
	def assertParses(self, code, msg = None):
		self.assertNotIn(self.p.parse(code), (None, []), msg)
	
	def assertNotParses(self, code, msg = None):
		with self.assertRaises(ParseException):
			self.p.parse(code)
	
	def assertTree(self, ast, tree = [], msg = None):
		if isinstance(ast, str):
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
		code = '// One line Comment\n  '
		self.assertParses(code)
