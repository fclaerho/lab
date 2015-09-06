# copyright (c) 2014-2015 fclaerhout.fr, released under the MIT license.

"""
Simple filesystem-like container.

Notes:
  * You can use the default root (see example) or define a new `path.Root()`.
  * a node can only be mounted once, use link() otherwise
  * node.path is resolved only if the node is mounted

Example:
	>>> import path
	>>> foo = path.Node("foo")
	>>> path.mount("/", foo)
	>>> path.list("/")
	("foo",)
	>>> path.exists("/foo")
	True
	>>> path.get("/foo")
	<Node foo>
	>>> path.umount("/foo")
"""

import threading, weakref

class NoSuchName(Exception): pass

class NameExists(Exception): pass

def _deref(node):
	return node.node_ref() if isinstance(node, Link) else node

def Path(obj):
	assert isinstance(obj, (str, unicode)), "%s: invalid path" % repr(obj)
	return obj

class Node(object):

	def __init__(self, name):
		self._parentref = None
		self._children = {}
		self.name = name
		self.lock = threading.Lock()

	@property
	def path(self):
		with self.lock:
			assert self._parentref, "%s: unmounted node has no resolvable path" % self.name
			return self._parentref().path.rstrip("/") + "/" + self.name

	@property
	def root(self):
		with self.lock:
			if self._parentref:
				return self._parentref().root
			else:
				assert isinstance(self, Root), "%s: not a root" % self.name
				return self

	def mount(self, node):
		with self.lock:
			assert not node._parentref, "%s: cannot remount" % node.name
			if node.name in self._children:
				raise NameExists(node.name)
			self._children[node.name] = node
			node._parentref = weakref.ref(self)
			return node

	def link(self, node):
		return self.mount(Link(_deref(node)))

	def is_link(self, path):
		node, tail = self._split(path)
		return node.is_link(tail) if tail else isinstance(node, Link)

	def _split(self, path):
		"split a relative path '<name>/...' into a pair (children[<name>], '...')"
		if path.startswith(self.path):
			path = path.replace(self.path, "", 1)
			assert path, "cannot split current node path"
		if "/" in path:
			name, tail = path.split("/", 1)
		else:
			name, tail = path, None
		with self.lock:
			if not name in self._children:
				raise NoSuchName(name)
			return self._children[name], tail

	def umount(self, path, precondition = None):
		path = Path(path)
		child, tail = self._split(path)
		if tail:
			return child.umount(tail, precondition = precondition)
		else:
			with self.lock:
				child = _deref(child)
				assert not precondition or precondition(child), "%s: umount precondition violated" % path
				del self._children[child.name]
				child._parentref = None
				return child

	def get(self, path):
		"return the node at path"
		path = Path(path)
		if path == self.path:
			return self
		else:
			child, tail = self._split(path)
			return child.get(tail) if tail else _deref(child)

	def select(self, by_value = False, predicate = None, key = None, reverse = False):
		with self.lock:
			predicate = predicate or (lambda node: True)
			pairs = [(name, _deref(node)) for name, node in self._children.items() if predicate(_deref(node))]
			if key:
				pairs.sort(key = lambda pair: key(pair[1]), reverse = reverse)
			if by_value:
				return tuple(node for _, node in pairs)
			else:
				return tuple(name for name, _ in pairs)

	def __div__(self, obj):
		"syntactic sugar to build paths, e.g. <node> / <str> => path"
		if isinstance(obj, (str, unicode)):
			assert not obj.startswith("/")
			return self.path + "/" + obj
		else:
			raise TypeError

class Root(Node):

	@property
	def path(self): return "/"

class Link(Node):

	def __init__(self, node):
		super(Link, self).__init__(node.name)
		self.node_ref = weakref.ref(node)

class Null(Node):

	def mount(self, node):
		return node

	def link(self, node):
		return node

__root = Root("__root")

def get(path):
	return __root.get(path)

def link(path, node):
	return __root.get(path).link(node)

def is_link(path):
	return __root.is_link(path)

def reset():
	__root._children = {}

def mount(path, node):
	return __root.get(path).mount(node)

def umount(path, precondition = lambda node: True):
	return __root.umount(path, precondition = precondition)

def select(path, by_value = False, predicate = None, key = None, reverse = False):
	return __root.get(path).select(by_value = by_value, predicate = predicate, key = key, reverse = reverse)

def exists(path):
	try:
		__root.get(path)
		return True
	except NoSuchName:
		return False
