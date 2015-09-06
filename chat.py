# copyright (c) 2014-2015 fclaerhout.fr, released under the MIT license.

"Minimalist P2P REST chat framework"

__version__ = "1.0"

import wsgiref.simple_server, threading, readline, unittest, httplib, weakref, time, sys, re

import bottle, strfmt # 3rd-party

#########
# model #
#########

class Agent(object):

	def __init__(self, name):
		self.peers = {} # dict of weak references
		self.name = name

	def _get_peername(self, peer):
		for name in self.peers:
			if self.peers[name]() == peer:
				return name

	def echo(self, name, obj): pass

	def _receive(self, source, obj):
		"do not call directly -- invoked by send"
		name = self._get_peername(source)
		assert name, "%s: unknown peer" % source
		self.echo(name, obj)

	def send(self, name, obj):
		assert name in self.peers, "%s: unknown name" % name
		self.peers[name]()._receive(source = self, obj = obj)

	def broadcast(self, obj):
		assert self.peers, "no registered peer"
		for name in self.peers:
			self.send(name, obj)

	def _join(self, peer):
		"do not call directly -- invoked by add"
		name = peer.name
		while name in self.peers:
			name = "_%s" % name
		assert not self._get_peername(peer), "%s: peer already registered" % peer
		self.peers[name] = weakref.ref(peer)
		self.echo(name, "joined")

	def add(self, name, peer):
		assert self.name != name, "%s: name already used (by you)" % name
		assert name not in self.peers, "%s: name already used" % name
		assert not self._get_peername(peer), "%s: peer already registered" % peer
		self.peers[name] = weakref.ref(peer)
		peer._join(self)

	def _leave(self, peer):
		"do not call directly -- invoked by remove"
		# called from __del__(), weakref() is None:
		up = {}
		down = []
		for name in self.peers:
			if self.peers[name]() is None:
				down.append(name)
			else:
				up[name] = self.peers[name]
		self.peers = up
		for name in down:
			self.echo(name, "disconnected")
		# regular call from remove():
		name = self._get_peername(peer)
		if name:
			del self.peers[name]
			self.echo(name, "left")

	def remove(self, name, force = False):
		assert name in self.peers, "%s: unknown peer" % name
		peer = self.peers[name]()
		del self.peers[name]
		peer._leave(self)

	def __del__(self):
		for name in self.peers:
			self.peers[name]()._leave(self) # notify peers we're leaving

#######################
# REST implementation #
#######################

class RestPeer(object):
	"handle http emission"

	cache = [] # strong references to peers

	def __init__(self, name, host, port):
		self.name = name
		self.host = host
		self.port = port
		self.cnx = httplib.HTTPConnection(host = self.host, port = self.port)
		RestPeer.cache.append(self)

	def __str__(self):
		return "%s at %s:%s" % (self.name, self.host, self.port)

	def __eq__(self, other):
		return self.host == other.host and self.port == other.port

	def __ne__(self, other):
		return not (self == other)

	def __http_send(self, path, source, obj):
		body = repr(obj) if obj else None
		headers = {
			"X-agent-name": source.name,
			"X-agent-host": source.host,
			"X-agent-port": source.port,
		}
		try:
			self.cnx.request("POST", path, body, headers)
			res = self.cnx.getresponse()
		except Exception as e:
			raise Exception("%s: %s" % (self, e))

	def _receive(self, source, obj):
		self.__http_send(path = "/receive", source = source, obj = obj)

	def _join(self, peer):
		self.__http_send(path = "/join", source = peer, obj = None)

	def _leave(self, peer):
		self.__http_send(path = "/leave", source = peer, obj = None)

class WSGIRefServer(bottle.ServerAdapter):
	"stoppable wsgi server adapter"

	def __init__(self, *args, **kwargs):
		super(WSGIRefServer, self).__init__(*args, **kwargs)
		class QuietHandler(wsgiref.simple_server.WSGIRequestHandler):
			def log_request(*args, **kw): pass
		self.options['handler_class'] = QuietHandler
		self.server = None

	def run(self, handler):
		self.server = wsgiref.simple_server.make_server(
			host = self.host,
			port = self.port,
			app = handler,
			**self.options)
		self.server.serve_forever()

	def running(self):
		return self.server

	def shutdown(self):
		if self.running():
			self.server.shutdown()

class RestAgent(Agent):
	"handle asynchronous shell and http reception"

	def __init__(self, name, host, port):
		super(RestAgent, self).__init__(name = name)
		self.host = host
		self.port = port
		self.server = WSGIRefServer(host = host, port = port)
		proxy = weakref.proxy(self)
		bottle.route("/receive", "POST", lambda *args: proxy._http_receive(*args))
		bottle.route("/leave", "POST", lambda *args: proxy._http_leave(*args))
		bottle.route("/join", "POST", lambda *args: proxy._http_join(*args))
		self.t = threading.Thread(
			target = bottle.run,
			kwargs = {"server": self.server, "quiet": True})
		self.t.daemon = True
		self.t.start()
		while not self.server.running(): continue # active wait

	def __del__(self):
		self.server.shutdown()
		self.t.join()
		super(RestAgent, self).__del__()

	def _http_recv(self):
		name = bottle.request.headers.get("X-agent-name")
		host = bottle.request.headers.get("X-agent-host")
		port = bottle.request.headers.get("X-agent-port")
		peer = RestPeer(name = name, host = host, port = port)
		body = bottle.request.body.read()
		obj = eval(body) if body else None
		return (peer, obj)

	def _http_receive(self):
		peer, obj = self._http_recv()
		self._receive(source = peer, obj = obj)

	def _http_join(self):
		peer, obj = self._http_recv()
		self._join(peer = peer)

	def _http_leave(self):
		peer, obj = self._http_recv()
		self._leave(peer = peer)

	def prompt(self):
		return strfmt.yellow("%s> ") % self.name

	def echo(self, name, obj):
		"clear current line, print obj from peer"
		prefix = "[%s] %s:" % (time.strftime("%H:%m"), name)
		for idx, line in enumerate(("%s" % obj).splitlines()):
			if not idx:
				print strfmt.gray("\033[2K\033[1G%s %s") % (prefix, line)
			else:
				print " " * len(prefix), strfmt.gray(line)
		if threading.current_thread() == self.t:
			buffer = readline.get_line_buffer()
			if buffer and not buffer.endswith("\n"):
				sys.stdout.write("%s%s" % (self.prompt(), buffer))
				sys.stdout.flush()
			else:
				sys.stdout.write(self.prompt())
				sys.stdout.flush()

	def shell(self):
		print strfmt.gray("Hi %s, Press ^C or type /quit to quit.") % self.name
		try:
			while True:
				line = raw_input(self.prompt()).strip()
				try:
					if line.startswith("@"):
						self._handle_msg(line)
					elif line.startswith("/"):
						self._handle_cmd(line)
					elif line:
						self.broadcast(obj = line)
				except Exception as e:
					self.echo("<!> error", e)
		except SystemExit: pass
		except KeyboardInterrupt: print
		print strfmt.gray("bye!")

	def _handle_msg(self, line):
		name = line[1:line.index(" ")]
		msg = line[line.index(" "):].strip()
		self.send(name = name, obj = msg)

	def _handle_cmd(self, line):
		data = line.split()
		cmd = data[0][1:]
		if cmd == "help":
			print strfmt.gray("list: list peers")
			print strfmt.gray("add <name> <hostname> <port>: add peer")
			print strfmt.gray("del <name>: delete peer")
			print strfmt.gray("quit: terminate session")
		elif cmd == "list":
			for name in self.peers:
				print strfmt.gray("%s") % self.peers[name]()
		elif cmd == "add":
			name, host, port = data[1:]
			peer = RestPeer(name = name, host = host, port = port)
			self.add(name = name, peer = peer)
		elif cmd == "del":
			name, = data[1:]
			self.remove(name = name)
		elif cmd == "quit":
			quit()
		else:
			raise Exception("%s: unknown command, type /help for help" % cmd)

########
# test #
########

# test model
#############

class FakeAgent(Agent):

	def __init__(self, *args, **kwargs):
		super(FakeAgent, self).__init__(*args, **kwargs)
		self.received = None

	def echo(self, name, obj):
		self.received = (name, obj)

class BaseTest(unittest.TestCase):

	cls = FakeAgent

	def test_add_remove(self):
		foo = (self.cls)("foo")
		bar = (self.cls)("bar")
		foo.add("qux", bar)
		self.assertEqual(bar.received, ("foo", "joined"))
		foo.remove("qux")
		self.assertEqual(bar.received, ("foo", "left"))

	def test_add_del(self):
		foo = (self.cls)("foo")
		bar = (self.cls)("bar")
		foo.add("qux", bar) # -> bar._join(foo)
		self.assertEqual(bar.received, ("foo", "joined"))
		del bar # -> bar.__del__() -> foo._leave(bar)
		self.assertEqual(foo.received, ("qux", "disconnected"))

	def test_add_send(self):
		foo = (self.cls)("foo")
		bar = (self.cls)("bar")
		foo.add("qux", bar)
		foo.send("qux", "hello")
		self.assertEqual(bar.received, ("foo", "hello"))
		bar.send("foo", "hi")
		self.assertEqual(foo.received, ("qux", "hi"))

# test REST implementation
###########################

class RestAgentTestAdapter(RestAgent):

	port = 8000

	def __init__(self, name):
		super(RestAgentTestAdapter, self).__init__(
			name = name,
			host = "localhost",
			port = RestAgentTestAdapter.port)
		RestAgentTestAdapter.port += 1
		self.received = None

	def echo(self, name, obj):
		self.received = (name, obj)

class RestTest(BaseTest):

	timeout = 2

	cls = RestAgentTestAdapter

if __name__ == "__main__": unittest.main(verbosity = 2)
