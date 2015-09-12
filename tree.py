# copyright (c) 2014-2015 fclaerhout.fr, released under the MIT license.
# coding: utf-8

"""
List contents of directories in a tree-like format.

Usage:
  tree [options] [PATH]
  tree --help

Options:
  -x GLOBS, --exclude GLOBS  exclude matching nodes [default: .git]
  -m INT, --max-depth INT    set maximum depth [default: inf]
  -h, --help                 display full help text
  -2                         equivalent to -m 2
"""

import fnmatch, os

import docopt, utils # 3rd-party

class FSNode(object):

	def __init__(self, path, toplevel, maxdepth):
		self.path = path.rstrip("/")
		self.basename = os.path.basename(self.path)
		self.toplevel = toplevel
		self.maxdepth = maxdepth

	def __str__(self):
		name = self.basename.decode("utf-8", errors = "ignore")
		return utils.blue("%s/") % name if self.is_directory() else name

	def is_directory(self):
		return os.path.isdir(self.path)

	def is_readable(self):
		return os.access(self.path, os.R_OK)

	def __iter__(self):
		if self.maxdepth and self.is_directory() and self.is_readable():
			for name in os.listdir(self.path):
				yield FSNode(
					os.path.join(self.path, name),
					toplevel = False,
					maxdepth = self.maxdepth - 1)

def main(args = None):
	opts = docopt.docopt(
		doc = __doc__,
		argv = args)
	root = FSNode(
		opts["PATH"] or ".",
		toplevel = True,
		maxdepth = 2 if opts["-2"] else float(opts["--max-depth"])) # float because inf is the default
	def noop(node): pass
	if opts["--exclude"]:
		def is_pre_prunable(node):
			return any(fnmatch.fnmatch(node.basename, glob) for glob in opts["--exclude"].split(","))
	else:
		is_pre_prunable = noop
	print utils.strtree(
		root,
		is_pre_prunable = is_pre_prunable,
		is_post_prunable = noop)
