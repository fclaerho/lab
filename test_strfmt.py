# copyright (c) 2014-2015 florent claerhout, released under the MIT license.
# coding: utf-8

import unittest

import strfmt # 3rd-party

class ClassTree(object):
	"make a class iterable over its sub-classes"

	def __init__(self, cls):
		assert type(cls) is type
		self.cls = cls

	__str__ = lambda self = True: self.cls.__name__

	def __iter__(self):
		for subcls in self.cls.__subclasses__():
			yield ClassTree(subcls)

class Test(unittest.TestCase):

	def test_strtree(self):
		class A(object): pass
		class B(A): pass
		class C(B): pass
		class D(B): pass
		class E(A): pass
		class F(A): pass
		class G(F): pass
		res = tuple(val.cls for val in ClassTree(A))
		self.assertEqual((B, E, F), res)
		self.assertEqual(utils.strtree(ClassTree(A)), unicode("""A
├─ B
│  ├─ C
│  └─ D
├─ E
└─ F
   └─ G""", "utf-8"))

	def test_strcolalign_with_text(self):
		text = "a:bbbbbb:c\naaa:b:c"
		out = "a    bbbbbb  c\naaa  b       c"
		self.assertEqual(utils.strcolalign(text), out)

	def test_strcolalign_with_table(self):
		tbl = (("a", "bbbbbb", "c"), ("aaa", "b", "c"))
		out = "a    bbbbbb  c\naaa  b       c"
		self.assertEqual(utils.strcolalign(tbl), out)

if __name__ == "__main__": unittest.main(verbosity = 2)
