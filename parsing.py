# copyright (c) 2014-2015 fclaerhout.fr, released under the MIT license.

"simple topdown backtracking parsing framework"

__version__ = "0.1"

import unittest, sys

##################################################
# parsing source ~ behave like an array of bytes #
##################################################

class EOL:
	"end of line combinations"
	LF = "\n"     # *nix, ...
	CR = "\r"     # old osx
	LFCR = "\n\r" # wut?
	CRLF = "\r\n" # win
	RS = "\x1E"   # old qnx

class Source(object):
	"extend object with parsing support routines: top, shift, save, restore"

	class FileAdapter(object):

		def __init__(self, fp):
			self.fp = fp

		def __len__(self):
			self.fp.seek(0, 2)
			return self.fp.tell()

		def __getitem__(self, i):
			self.fp.seek(i, 0)
			return self.fp.read(1)

	line = 1 # current line
	cur = 0  # current reading position

	def __init__(self, obj, is_path = False, eol = EOL.LF):
		"$obj may be a string, file pointer or path"
		if isinstance(obj, str):
			if is_path:
				self.obj = Source.FileAdapter(open(obj, "r"))
			else:
				self.obj = obj
		elif isinstance(obj, file):
			self.obj = Source.FileAdapter(obj)
		self.eol = eol

	__len__ = lambda self: len(self.obj)

	is_eof = lambda self: self.cur >= len(self.obj)

	top = lambda self: False if self.is_eof() else self.obj[self.cur]

	def is_eol(self):
		if len(self.eol) == 1:
			return self.top() == self.eol
		elif len(self.eol) == 2:
			if self.cur + 1 < len(self.obj):
				return self.obj[self.cur:self.cur + 2] == self.eol
			else:
				return False
		else:
			raise NotImplementedError("overlong end-of-line sequence")

	def shift(self):
		if self.is_eof():
			pass
		elif self.is_eol():
			self.line += 1
			self.cur += len(self.eol)
		else:
			self.cur += 1

	def save(self):
		self.saved_cur = self.cur
		self.saved_line = self.line

	def restore(self):
		self.line = self.saved_line
		self.cur = self.saved_cur

##################
# core exception #
##################

class ParseError(Exception):

	def __init__(self, rule, src):
		msg = "line %i: at pos %i, '%s': expected %s" % (
			src.line,
			src.cur,
			src.top() or "(eof)",
			rule)
		super(ParseError, self).__init__(msg)

#########
# token #
#########

class Token(object):

	def __init__(self, val):
		self.val = val

	__eq__ = lambda self, other: self.val == other

	__ne__ = lambda self, other: not (self == other)

	__str__ = lambda self: self.val

	__iter__ = lambda self: (_ for _ in ())

	def __iadd__(self, val):
		self.val += val
		return self

class PairToken(Token):

	def __init__(self, key, value):
		self.key = key
		self.value = value

	__str__ = lambda self: "%s = %s" % (self.key, self.value)

	def __iadd__(self, other):
		raise NotImplementedError()

class NodeToken(Token):

	def __init__(self, name, *tokens):
		self.name = name
		self.tokens = tokens or []

	__eq__ = lambda self, other: self.tokens == other

	__str__ = lambda self: self.name

	__iter__ = lambda self: (t for t in self.tokens)

	def __iadd__(self, t):
		if t:
			self.tokens.append(t)
		return self

	__getitem__ = lambda self, i: self.tokens[i]

##############
# core rules #
##############

class Rule(object):
	"base rule"

	token = None

	__repr__ = lambda self, s: "%s(%s)" % (type(self).__name__, s)

	def parse(self, src):
		"parse input, set self.token and return self or raise ParseError"
		raise NotImplementedError()

	def skip_blanks(self, src):
		while src.top() and src.top().isspace(): src.shift()

	def skip_line(self, src):
		while src.top() and not src.is_eol(): src.shift()

class And(Rule):
	"parse conjunction of rules"

	def __init__(self, *rules):
		self.rules = rules

	__repr__ = lambda self: super(And, self).__repr__("%s" % (self.rules,))

	def parse(self, src):
		self.token = NodeToken("<and>")
		for r in self.rules:
			self.token += r.parse(src).token
		return self

class Or(Rule):
	"parse disjunction of rules"

	def __init__(self, *rules):
		self.rules = rules

	__repr__ = lambda self: super(Or, self).__repr__("%s" % (self.rules,))

	def parse(self, src):
		src.save()
		for r in self.rules:
			try:
				self.token = r.parse(src).token
				return self
			except ParseError:
				src.restore()
		else:
			raise ParseError(self, src)

class Character(Rule):
	"parse character"

	def __init__(self, char, keep_blanks = False):
		self.char = char
		self.keep_blanks = keep_blanks

	__repr__ = lambda self: super(Character, self).__repr__("'%s'" % self.char)

	def parse(self, src):
		if not self.keep_blanks:
			self.skip_blanks(src)
		if src.top() == self.char:
			src.shift()
		else:
			raise ParseError(self, src)
		self.token = Token(self.char)
		return self

class String(Rule):
	"parse string"

	def __init__(self, string, keep_blanks = False):
		self.string = string
		self.keep_blanks = keep_blanks

	__repr__ = lambda self: super(String, self).__repr__("%s" % self.string)

	def parse(self, src):
		if not self.keep_blanks:
			self.skip_blanks(src)
		for c in self.string:
			if src.top() == c:
				src.shift()
			else:
				raise ParseError(self, src)
		self.token = Token(self.string)
		return self

class Digits(Rule):
	"parse consecutive digits"

	def __init__(self, keep_blanks = False):
		self.keep_blanks = keep_blanks

	def parse(self, src):
		if not self.keep_blanks:
			self.skip_blanks(src)
		self.token = Token("")
		if not src.top() or not src.top().isdigit():
			raise ParseError(self, src)
		while src.top() and src.top().isdigit():
			self.token += src.top()
			src.shift()
		return self

class Alphas(Rule):
	"parse consecutive alphabetic characters"

	def parse(self, src):
		self.skip_blanks(src)
		self.token = Token("")
		if not src.top() or not src.top().isalpha():
			raise ParseError(self, src)
		while src.top() and src.top().isalpha():
			self.token += src.top()
			src.shift()
		return self

class Alnums(Rule):
	"parse consecutive alphanumeric characters"

	def __init__(self, eset = ""): # ExtensionSET: supplementary chars
		self.eset = eset

	def parse(self, src):
		self.skip_blanks(src)
		self.token = Token("")
		if not src.top() or not (src.top().isalnum() or src.top() in self.eset):
			raise ParseError(self, src)
		while src.top() and (src.top().isalnum() or src.top() in self.eset):
			self.token += src.top()
			src.shift()
		return self

class Block(Rule):
	"parse characters enclosed between delimiters $head and $tail"

	def __init__(self, head, tail):
		self.head = head
		self.tail = tail

	__repr__ = lambda self: super(Block, self).__repr__("%s...%s" % (self.head, self.tail))

	def parse(self, src):
		self.token = Token("")
		String(self.head).parse(src)
		while src.top():
			src.save()
			try:
				String(self.tail, keep_blanks = True).parse(src)
				return self
			except ParseError:
				src.restore()
				self.token += src.top()
				src.shift()
		raise ParseError(self, src)

class Line(Rule):
	"parse characters until EOL or a specified character on the line"

	def __init__(self, char = None):
		self.char = char

	def parse(self, src):
		self.token = Token("")
		while src.top() and not (src.top() == self.char or src.is_eol()):
			self.token += src.top()
			src.shift()
		src.shift() # skip tail
		return self

class Many(Rule):
	"parse $rule, iterate until mismatch"

	def __init__(self, rule):
		self.rule = rule

	def parse(self, src):
		self.token = NodeToken("<many>")
		while True:
			src.save()
			try:
				self.token += self.rule.parse(src).token
			except ParseError:
				src.restore()
				break
		return self

class Repeat(Rule):
	"parse $rule, iterate until EOF"

	def __init__(self, rule):
		self.rule = rule

	def parse(self, src):
		self.token = NodeToken("<repeat>")
		while src.top():
			self.token += self.rule.parse(src).token
			self.skip_blanks(src)
		return self

class List(Rule):
	"parse non-empty list of $sep_rule-separated $item_rule items"

	def __init__(self, item_rule, sep_rule):
		self.item_rule = item_rule
		self.sep_rule = sep_rule

	def parse(self, src):
		self.token = NodeToken("<list>")
		while True:
			self.token += self.item_rule.parse(src).token
			src.save()
			try:
				self.sep_rule.parse(src)
			except ParseError:
				src.restore()
				return self

####################
# concrete parsers #
####################

class Parser(Rule): pass

class Ini(Parser):
	"parse .ini file"

	class Comment(Rule):

		def parse(self, src):
			self.skip_blanks(src)
			if src.top() == "#":
				self.skip_line(src)
			else:
				raise ParseError(self, src)
			return self

	class Pair(Rule):

		def parse(self, src):
			self.key = "%s" % Alnums("-_").parse(src).token
			Or(Character("="), Character(":")).parse(src)
			self.val = "%s" % LineUntil().parse(src).token
			# handle multilines:
			while src.top() == "\t":
				self.skip_blanks(src)
				self.val += " %s" % LineUntil().parse(src).token
			self.val = self.val.strip()
			self.token = PairToken(self.key, self.val)
			return self

	class Section(Rule):

		def parse(self, src):
			self.skip_blanks(src)
			self.name = "%s" % Block("[", "]").parse(src).token
			self.pairs = Many(Or(Ini.Pair(), Ini.Comment())).parse(src).token
			self.token = NodeToken(self.name, self.pairs)
			return self

	def parse(self, src):
		self.token = Repeat(Or(Ini.Comment(), Ini.Section())).parse(src).token
		return self

#########
# tests #
#########

class RuleTest(unittest.TestCase):

	def test_shift_LF(self):
		s = Source("aaa\nbbb\nccc", eol = EOL.LF)
		while not s.is_eof():
			s.shift()
		self.assertEqual(s.line, 3)

	def test_shift_CRLF(self):
		s = Source("aaa\r\nbbb\r\nccc", eol = EOL.CRLF)
		while not s.is_eof():
			s.shift()
		self.assertEqual(s.line, 3)

	def test_character(self):
		s = Source("abc")
		self.assertEqual(Character("a").parse(s).token, "a")
		self.assertEqual(Character("b").parse(s).token, "b")
		self.assertEqual(Character("c").parse(s).token, "c")
		self.assertRaises(ParseError, Character("d").parse, s)
		self.assertFalse(s.top())

	def test_digits(self):
		s = Source("42 666")
		r = Digits()
		self.assertEqual(r.parse(s).token, "42")
		self.assertEqual(r.parse(s).token, "666")

	def test_and(self):
		s = Source("foo bar baz")
		r = And(
			String("foo"),
			String("bar"),
			String("baz"),
		)
		r.parse(s)

	def test_or(self):
		s = Source("bar")
		r = Or(
			String("foo"),
			String("bar"),
			String("baz"),
		)
		r.parse(s)
		self.assertEqual(r.token, "bar")

	def test_block(self):
		data = " lorem ipsum "
		s = Source("{%s}" % data)
		r = Block("{", "}")
		r.parse(s)
		self.assertEqual(r.token, data)

	def test_many(self):
		s = Source("bar bar bar bar")
		r = Repeat(String("bar"))
		self.assertEqual(r.parse(s).token, ["bar"] * 4)
		self.assertFalse(s.top())

	def test_line(self):
		s = Source("aaaa\nbbbb")
		r = Line()
		self.assertEqual(r.parse(s).token, "aaaa")
		self.assertEqual(r.parse(s).token, "bbbb")

if __name__ == "__main__": unittest.main(verbosity = 2)
