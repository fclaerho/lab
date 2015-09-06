# copyright (c) 2014-2015 florent claerhout, released under the MIT license.

"HTML5 bootstrap-based toolkit"

__version__ = "0.1"

import textwrap, unittest, weakref, os

###########
# helpers #
###########

def flatten(text):
	return "".join(line.strip() for line in ("%s" % text).splitlines())

def indent(level, text):
	return "\n".join((("  " * level) + line if line else line) for line in ("%s" % text).splitlines())

class Element(object):
	"generic XML element with pretty-printing support"

	def __init__(self, name, *children, **attributes):
		self.parent = None
		self.name = name
		self.children = []
		self.attributes = attributes
		self.collapsable = True # if True, support <foo/> syntax, otherwise <foo></foo> only.
		for child in children:
			self.append(child)

	def add_class(self, cls):
		if "class" in self.attributes:
			self.attributes["class"] += " %s" % cls
		else:
			self.attributes["class"] = "%s" % cls

	def copy(self):
		elm = Element(
			self.name,
			*[(child.copy() if isinstance(child, Element) else child) for child in self.children],
			**self.attributes)
		elm.collapsable = self.collapsable
		return elm

	def __eq__(self, other):
		return\
			self.name == other.name\
			and self.children == other.children\
			and self.attributes == other.attributes

	def __ne__(self, other):
		return not (self == other)

	def __str__(self):
		"render XML code"
		attributes = []
		for key, value in self.attributes.items():
			if value is None:
				attributes.append("%s" % key)
			else:
				attributes.append("%s='%s'" % (key, value))
		vars = {
			"name": self.name,
			"sp": " " if self.attributes else "",
			"attributes": " ".join(attributes),
			"children": indent(1, "\n".join("%s" % child for child in self.children)),
		}
		if self.children:
			return (textwrap.dedent("""
				<%(name)s%(sp)s%(attributes)s>
				%(children)s
				</%(name)s>
			""") % vars).strip()
		elif self.collapsable:
			return "<%(name)s%(sp)s%(attributes)s />" % vars
		else:
			return "<%(name)s%(sp)s%(attributes)s></%(name)s>" % vars

	#
	# list behavior over children
	#

	def __iter__(self):
		"iterate over children"
		for child in self.children:
			yield child

	def __contains__(self, child):
		return child in self.children\
			or any(child in c for c in self.children if isinstance(c, Element))

	def append(self, child):
		self.children.append(child)
		if isinstance(child, Element):
			child.parent = weakref.ref(self)

	def insert(self, idx, child):
		self.children.insert(idx, child)

	def __gt__(self, child):
		self.append(child)
		return child

	@property
	def root(self):
		cur = self
		while cur.parent and cur.parent():
			cur = cur.parent()
		return cur

	@property
	def last_child(self):
		return self.children[-1]

	@property
	def first_child(self):
		return self.children[0]

	#
	# dict behavior over attributes
	#

	def __setitem__(self, key, value):
		"set attribute on string key, set child on int key"
		if isinstance(key, int):
			self.children[key] = value
		else:
			self.attributes[key] = value

	def __getitem__(self, key):
		"get attribute on string key, get child on int key"
		if isinstance(key, int):
			return self.children[key]
		else:
			return self.attributes[key]

	def keys(self):
		return self.attributes.keys()

	def items(self):
		return self.attributes.items()

	def values(self):
		return self.attributes.values()

def ExternalScript(url):
	elm = Element(
		"script",
		src = url)
	elm.collapsable = False
	return elm

def Script(content):
	return Element(
		"script",
		content)

def ExternalStyleSheet(url):
	return Element(
		"link",
		rel = "stylesheet",
		href = url)

##################
# implementation #
##################

URL = {
	"bs": "http://netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css",
	"js": "http://netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js",
	"jq": "https://ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js",
}

class Document(object):

	def __init__(
		self,
		title,
		lang = "en",
		charset = "utf-8",
		headers = None,
		*children):
		self.title = title
		self.lang = lang
		self.charset = charset
		self.parent = None
		self.headers = headers or ()
		self.children = list(children)

	def __str__(self):
		title = Element("title", self.title)
		charset = Element("meta", charset = "utf-8")
		viewport = Element(
			"meta",
			NAME = "viewport",
			content = "width=device-width, initial-scale=1")
		style_sheet = ExternalStyleSheet(url = URL["bs"])
		head = Element("head", title, charset, viewport, style_sheet)
		for hdr in self.headers:
			head.append(hdr)
		for idx, cld in enumerate(self.children):
			if cld.name == "script":
				break
		else:
			idx = 0
		self.children.insert(idx, ExternalScript(url = URL["jq"]))
		self.children.insert(idx + 1, ExternalScript(url = URL["js"]))
		body = Element("body", *self.children)
		html = Element("html", head, body, lang = self.lang)
		return "<!doctype html>\n%s" % html

	def append(self, child):
		self.children.append(child)
		if isinstance(child, Element):
			child.parent = weakref.ref(self)

	def insert(self, idx, child):
		self.children.insert(idx, child)

	def __gt__(self, child):
		self.append(child)
		return child

class Navbar(object): pass

class Container(Element):
	"a container is a list of rows, each row is a list of columns"

	def __init__(self, fluid = False):
		super(Container, self).__init__(
			"div",
			**{"class": "container-fluid" if fluid else "container"})

	def newline(self):
		row = Element("div", **{"class": "row"})
		row.parent = weakref.ref(self)
		self.children.append(row)
		self.size = 12

	def shift(self, offset = 0, span = 1):
		if not self.children:
			self.newline()
		assert offset + span <= self.size
		elm = Element("div")
		elm.add_class("col-md-offset-%i" % offset)
		elm.add_class("col-md-%i" % span)
		self.last_child.append(elm)
		self.size -= offset + span

	def append(self, child):
		self.last_child.last_child.append(child)
		if isinstance(child, Element):
			child.parent = weakref.ref(self.last_child.last_child)

#####################################
# typography                        #
# http://getbootstrap.com/css/#type #
#####################################

def Heading(level, primary, secondary = None):
	assert 1 <= level <= 6
	children = [primary]
	if secondary:
		children.append(Element("small", secondary))
	return Element("h%i" % int(level), *children)

def P(*children):
	return Element("p", *children)

def Lead(*children):
	"Make a paragraph stand out"
	return Element("p", *children, **{"class": "lead"})

def Mark(*children):
	"For highlighting a run of text due to its relevance in another context"
	return Element("mark", *children)

def Del(*children):
	"For indicating blocks of text that have been deleted"
	return Element("del", *children)

def S(*children):
	"For indicating blocks of text that are no longer relevant"
	return Element("s", *children)

def Ins(*children):
	"For indicating additions to the document"
	return Element("ins", *children)

def U(*children):
	"To underline text"
	return Element("u", *children)

def Small(*children):
	"For de-emphasizing inline or blocks of text"
	return Element("small", *children)

def Strong(*children):
	"For emphasizing a snippet of text with a heavier font-weight"
	return Element("strong", *children)

def Em(*children):
	"For emphasizing a snippet of text with italics"
	return Element("em", *children)

def align_text(how, element):
	d = {
		"left": "text-left",
		"center": "text-center",
		"right": "text-right",
		"justify": "text-justify",
		"nowrap": "text-nowrap",
	}
	assert how in d, "%s: not in %s" % (how, d.keys())
	element.add_class(d[how])
	return element

def transform_text(how, element):
	d = {
		"lowercase": "text-lowercase",
		"uppercase": "text-uppercase",
		"capitalize": "text-capitalize",
	}
	assert how in d, "%s: not in %s" % (how, d.keys())
	element.add_class(d[how])
	return element

########################################
# buttons                              #
# http://getbootstrap.com/css/#buttons #
########################################

def Link(url):
	return Element("a", href = url)

def Download(url):
	return Element("a", href = url, download = None)

def Button(type, *children):
	return Element(
		"button",
		*children,
		**{
			"type": "button",
			"class": "btn btn-%s" % type,
		})

def set_button_size(size, btn):
	assert size in ("lg", "sm", "xs")
	btn.add_class("btn-%s" % size)
	return btn

class button:

	@staticmethod
	def Default(*children):
		return Button("default", *children)

	@staticmethod
	def Primary(*children):
		return Button("primary", *children)

	@staticmethod
	def Success(*children):
		return Button("success", *children)

	@staticmethod
	def Info(*children):
		return Button("success", *children)

	@staticmethod
	def Warning(*children):
		return Button("warning", *children)

	@staticmethod
	def Danger(*children):
		return Button("danger", *children)

	@staticmethod
	def Link(*children):
		return Button("link", *children)

################################################
# progress bar                                 #
# http://getbootstrap.com/components/#progress #
################################################

def Progress(type, min, cur, max):
	percent = (max - min) / 100 * cur
	elm = Element(
		"div",
		"%g%%" % percent,
		**{
			"class": "progress-bar progress-bar-%s" % type,
			"role": "progressbar",
			"aria-valuemin": "%i" % min,
			"aria-valuenow": "%i" % cur,
			"aria-valuemax": "%i" % max,
			"style": "width: %g%%" % percent,
		})
	return Element(
		"div",
		elm,
		**{"class": "progress"})

class progress:

	@staticmethod
	def Success(*args, **kwargs):
		return Progress("success", *args, **kwargs)

	@staticmethod
	def Info(*args, **kwargs):
		return Progress("info", *args, **kwargs)

	@staticmethod
	def Warning(*args, **kwargs):
		return Progress("warning", *args, **kwargs)

	@staticmethod
	def Danger(*args, **kwargs):
		return Progress("danger", *args, **kwargs)

##################################################
# glyphicons                                     #
# http://getbootstrap.com/components/#glyphicons #
##################################################

def Icon(name):
	return Element("span", **{"class": "glyphicon glyphicon-%s" % name})

class icon:

	@staticmethod
	def Asterisk():
		return Icon("asterisk")

	@staticmethod
	def Plus():
		return Icon("plus")

	@staticmethod
	def Euro():
		return Icon("euro")

	@staticmethod
	def Minus():
		return Icon("minus")

	@staticmethod
	def Cloud():
		return Icon("cloud")

	@staticmethod
	def Envelope():
		return Icon("envelope")

	@staticmethod
	def Pencil():
		return Icon("pencil")

	@staticmethod
	def Glass():
		return Icon("glass")

	@staticmethod
	def Music():
		return Icon("music")

	@staticmethod
	def Search():
		return Icon("search")

	@staticmethod
	def Heart():
		return Icon("heart")

	@staticmethod
	def Star():
		return Icon("star")

	@staticmethod
	def StarEmpty():
		return Icon("star-empty")

	@staticmethod
	def User():
		return Icon("user")

	@staticmethod
	def Film():
		return Icon("film")

	@staticmethod
	def ThLarge():
		return Icon("th-large")

def on_click(element, callback):
	element.attributes.update({"id": id(element)})
	path = "/event/on_click_%s" % id(element)
	doc = element.root
	doc.app.route(
		path = path,
		method = "GET",
		callback = callback)
	vars = {
		"id": id(element),
		"path": path,
	}
	script = """
	$("#%(id)s").click(function() {
		$.ajax({
			url: "%(path)s",
			success: function(data) {
				console.log("click %(id)s...");
			},
			complete: function() {}
		});
	})
	""" % vars
	doc > Script(textwrap.dedent(script).strip())

def update(element, callback, rate):
	element.attributes.update({"id": id(element)})
	path = "/event/update_%s" % id(element)
	doc = element.root
	doc.app.route(
		path = path,
		method = "GET",
		callback = callback)
	vars = {
		"id": id(element),
		"path": path,
		"rate": rate, # Hz
	}
	script = """
		(function update_%(id)i() {
			$.ajax({
				url: "%(path)s/html",
				success: function(data) {
					$("#%(id)i").html(data);
				},
				complete: function() {
					setTimeout(update_%(id)i, 1 / %(rate)g);
				}
			});
		})();
	""" % vars
	doc > Script(textwrap.dedent(script).strip())

#########
# tests #
#########

class ElementTest(unittest.TestCase):

	def test_empty(self):
		e = Element("foo")
		self.assertEqual("%s" % e, "<foo/>")

	def test_empty_with_attributes(self):
		e = Element("foo", bar = "baz", ans = "42")
		self.assertEqual("%s" % e, "<foo bar='baz' ans='42'/>")

	def test_with_children(self):
		e = Element("foo", Element("bar"), Element("baz"), Element("qux"))
		self.assertEqual("%s" % e, "<foo>\n  <bar/>\n  <baz/>\n  <qux/>\n</foo>")

def example():
	p = Document("hello")
	c = p > Container()
	c.shift(4, span = 4)
	c > Heading(1, "foo", "bar")
	c > Lead("hi there!")
	b = c > button.Danger(icon.Cloud(), "clickme")
	c.newline()
	c.shift(8, span = 4)
	c > Lead("hoy hoy")
	c > progress.Success(0, 45, 100)
	def f():
		print "hello"
	on_click(b, f)
	p.serve()

example()
