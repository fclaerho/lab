# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

import threading, unittest, random, time, sys

import path # 3rd-party

class Test(unittest.TestCase):

	def setUp(self):
		path.reset()

	def tearDown(self):
		path.reset()

	def test_depth_zero(self):
		self.assertEqual(path.select("/"), ())

	def test_depth_one(self):
		foo = path.Node("foo")
		path.mount("/", foo)
		self.assertEqual(path.select("/"), ("foo",))
		self.assertTrue(path.exists("/foo"))
		path.umount("/foo")
		self.assertEqual(path.select("/"), ())

	def test_depth_two(self):
		foo = path.Node("foo")
		path.mount("/", foo)
		bar = path.Node("bar")
		path.mount("/foo", bar)
		self.assertTrue(path.exists("/foo/bar"))
		self.assertEqual(path.select("/foo"), ("bar",))
		self.assertEqual(path.get("/foo/bar"), bar)
		path.umount("/foo/bar")
		self.assertEqual(path.select("/foo"), ())
		self.assertEqual(path.select("/"), ("foo",))

	def test_select(self):
		class XNode(path.Node):
			def __init__(self, name, x):
				super(XNode, self).__init__(name)
				self.x = x
		foo = XNode("foo", 42)
		bar = XNode("bar", 100)
		baz = XNode("baz", 3.14)
		qux = XNode("qux", 50)
		path.mount("/", foo)
		path.mount("/", bar)
		path.mount("/", baz)
		path.mount("/", qux)
		self.assertEqual(set(path.select("/")), set(("foo", "bar", "baz", "qux")))
		self.assertEqual(set(path.select("/", by_value = True)), set((foo, bar, baz, qux)))
		self.assertEqual(
			path.select("/", predicate = lambda node: node.x < 100, key = lambda node: node.x),
			("baz", "foo", "qux"))

	def test_link(self):
		"""
		/
		+- foo
		   +- baz
		+- bar
		   +- foo@
		"""
		foo = path.mount("/", path.Node("foo"))
		self.assertFalse(path.is_link("/foo"))
		path.mount("/", path.Node("bar"))
		lfoo = path.link("/bar", foo)
		self.assertEqual(lfoo.path, "/bar/foo")
		self.assertEqual(path.get("/bar/foo"), foo)
		self.assertTrue(path.is_link("/bar/foo"))
		baz = path.mount("/bar/foo", path.Node("baz"))
		self.assertEqual(baz.path, "/foo/baz")
		path.umount("/bar/foo")
		self.assertEqual(path.get("/foo"), foo)

	def test_concurrent_access(self):
		"spawn $nb_threads threads where each thread iterates $nb_ops times mounting and unmounting a node from the root"
		nb_threads = 100
		nb_ops = 100
		root = path.Root("root")
		exceptions = []
		def f(i):
			node = path.Node("node%i" % i)
			for i in xrange(nb_ops):
				try:
					if node.name not in root.select():
						op = "@mount"
						root.mount(node)
					else:
						root.umount(node.name)
				except Exception as exc:
					exceptions.append(exc)
					print "!! oops... %s: %s: %s" % (op, type(exc).__name__, exc)
					break
		pool = [threading.Thread(target = lambda i = i: f(i)) for i in xrange(nb_threads)]
		map(lambda t: t.start(), pool)
		map(lambda t: t.join(), pool)
		self.assertFalse(exceptions)

if __name__ == "__main__": unittest.main(verbosity = 2)
