from __future__ import unicode_literals, division, absolute_import, print_function

import os

__author__ = "richard"
__created__ = "2013-05-15"

class KAMLImportError(Exception): pass

class PackageImporter(object):
	
	def __init__(self, search_paths, parser_kwargs = {}, memo = set()):
		self.search_paths = [os.path.abspath(path) for path in search_paths]
		self.parser_kwargs = parser_kwargs
		self.memo = memo
	
	def import_package(self, name):
		'''
		Imports a file, and returns its AST
		'''
		parts = name.split(':')
		
		if parts[-1] == '*':
			parts = parts[:-1]
		#print ("<name={}>Parts={}".format(name, parts))
		parts[-1] += '.kaml'
		
		for path in self.search_paths:
			file_path = os.path.join(*([path] + parts))
			print("Trying to import {}".format(file_path))
			if file_path in self.memo:
				raise KAMLImportError("Already imported {}".format(file_path))
			
			try:
				with open(file_path) as fp:
					from .recdec import Parser
					
					self.memo.add(file_path)
					
					p = Parser(importer_memo = self.memo, **self.parser_kwargs)
					return p.parse(fp.read())
			except IOError:
				pass
		
		raise KAMLImportError("Could not find `{}` in search paths {}".format(name, self.search_paths))
