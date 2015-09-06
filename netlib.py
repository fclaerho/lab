# copyright (c) 2014-2015 fclaerhout.fr, released under the MIT license.
# coding: utf-8

"networking calculation functions and classes"

import math, re

####################
# support routines #
####################

def ip4_to_int32(a, b, c, d):
	assert all((0 <= i <= 255) for i in (a, b, c, d))
	return (a << 24) | (b << 16) | (c << 8) | d

def ip4str_to_int32(string):
	return ip4_to_int32(*map(int, string.split(".")))

##############
# data model #
##############

def VlanID(value):
	# 12 bits, 0, 4095, 1002-1005 are reserved.
	value = int(value)
	assert 1 <= value < 1002 or 1005 < value <= 4094, "%s: invalid vid, see IEEE 802.1Q for details" % value
	return value

class InvalidIp4Initializer(Exception): pass

class Ip4(object):

	def __init__(self, *args):
		"""
		instanciate an Ip4 object from either:
		  * a string, e.g. Ip4("192.168.0.1")
		  * a 32-bit integer, e.g. Ip4(42)
		  * 4 bytes, e.g. Ip4(192, 168, 0, 1)
		"""
		if len(args) == 1:
			obj, = args
			if isinstance(obj, (str, unicode)):
				self.value = ip4str_to_int32(obj)
			elif isinstance(obj, int):
				assert 0 <= obj <= (2 ** 32)
				self.value = obj
			else:
				raise InvalidIp4Initializer(args)
		elif len(args) == 4:
			self.value = ip4_to_int32(*args)
		else:
			raise InvalidIp4Initializer(args)

	def split(self):
		return (
			self.value >> 24,
			(self.value >> 16) & 0xFF,
			(self.value >> 8) & 0xFF,
			self.value & 0xFF,
		)

	def __repr__(self):
		return "%s(%s)" % (type(self).__name__, self.value)

	def __str__(self):
		return "%i.%i.%i.%i" % self.split()

	def hex(self):
		return "%x.%x.%x.%x" % self.split()

	def __int__(self):
		return self.value

	def __hex__(self):
		return "0x%X" % self.value

	def __index__(self):
		return self.value # required for bin()

	def __add__(self, other):
		return Ip4(self.value + int(other))

	def __sub__(self, other):
		return Ip4(self.value - int(other))

	def __eq__(self, other):
		return self.value == int(other)

	def __ne__(self, other):
		return not (self == other)

	def __lt__(self, other):
		return self.value < int(other)

	def __le__(self, other):
		return self.value <= int(other)

	def __gt__(self, other):
		return self.value > int(other)

	def __ge__(self, other):
		return self.value >= int(other)

	# pre-1994 classful networks:

	def is_class_a(self):
		return bin(self.value)[3] == "0"

	def is_class_b(self):
		return bin(self.value)[3:].startswith("10")

	def is_class_c(self):
		return bin(self.value)[3:].startswith("110")

	def is_class_d(self):
		return bin(self.value)[3:].startswith("1110")

	def is_class_e(self):
		return bin(self.value)[3:].startswith("1111")

class Range(object):

	def __init__(self, first, last):
		assert first < last, "%s is not less that %s" % (first, last)
		self.first = first if isinstance(first, Ip4) else Ip4(first)
		self.last = last if isinstance(last, Ip4) else Ip4(last)

	def __str__(self):
		return "%s — %s" % (self.first, self.last)

	def __unicode__(self):
		return self.__str__().decode("utf-8")

	def __len__(self):
		return int(self.last) - int(self.first) + 1

	def __iter__(self):
		adr = self.first
		while adr <= self.last:
			yield adr
			adr = adr + 1

	def __contains__(self, other):
		assert isinstance(other, Ip4), "%s: expected Ip4" % type(other).__name__
		return self.first <= other <= self.last

	def __eq__(self, other):
		return self.first == other.first and self.last == other.last

	def __ne__(self, other):
		return not (self == other)

	def __le__(self, other):
		return self.last <= other.first

	def index(self, item):
		return int(item) - int(self.first)

class InvalidSubnetInitializer(Exception): pass

class Subnet(object):

	def __init__(self, *args):
		"""
		instanciate an Subnet object from either:
		  * a slash notation, e.g. Subnet("10/8")
		  * a pair (Ip4, prefix)
		"""
		if len(args) == 1:
			obj, = args
			if isinstance(obj, (str, unicode)):
				assert "/" in obj, "%s: no subnet prefix" % obj
				addr, prefix = obj.split("/")
				if re.match("^\d{1,3}$", addr):
					addr = "%s.0.0.0" % addr
				elif re.match("^\d{1,3}\.\d{1,3}$", addr):
					addr = "%s.0.0" % addr
				elif re.match("^\d{1,3}\.\d{1,3}\.\d{1,3}$", addr):
					addr = "%s.0" % addr
				self.netid = Ip4(addr)
				self.prefix = int(prefix)
			else:
				raise InvalidSubnetInitializer(args)
		elif len(args) == 2:
			self.netid, self.prefix = args
			assert isinstance(self.netid, Ip4)
			assert isinstance(self.prefix, int)
		else:
			raise InvalidSubnetInitializer(args)
		# post-checks:
		assert not (int(self.netid) % 2), "%s: netid is not even" % self.netid
		self.size = 2 ** (32 - self.prefix)
		self.bcastid = self.netid + (len(self) - 1)
		assert int(self.bcastid) % 2, "%s: bcastid is not odd" % self.bcastid

	def __eq__(self, other):
		return self.netid == other.netid and self.size == other.size

	def __ne__(self, other):
		return not (self == other)

	def __len__(self):
		return self.size

	def __str__(self):
		return "%s/%i" % (self.netid, self.prefix)

	def __getattr__(self, key):
		if key == "first":
			self.first = self.netid
			return self.first
		elif key == "last":
			self.last = self.bcastid
			return self.last
		else:
			raise AttributeError(key)

	def __iter__(self):
		for i in xrange(len(self)):
			yield self.netid + i

	def __contains__(self, other):
		if isinstance(other, Ip4):
			return self.netid <= other <= self.bcastid
		elif isinstance(other, Range):
			return self.netid <= other.first and other.last <= self.bcastid
		else:
			raise AssertionError("%s: expected Ip4 or Range" % type(other).__name__)

	def split(self, cnt):
		bits = int(math.log(cnt) / math.log(2))
		prefix = self.prefix + bits
		return tuple(Subnet(self.netid + (i << (32 - prefix)), prefix) for i in xrange(2 ** bits))

PRIVATE = (
	Subnet("10/8"),
	Subnet("172.16/12"),
	Subnet("192.168/16"))

LOOPBACK = (Subnet("127/8"),)
