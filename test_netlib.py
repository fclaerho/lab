# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

import unittest

import netlib # 3rd-party

class SelfTest(unittest.TestCase):

	def _test4(self, func):
		for i in xrange(0, 255):
			self.assertEqual(i, func(0, 0, 0, i))
		for i in xrange(0, 255):
			self.assertEqual(i << 8, func(0, 0, i, 0))
		for i in xrange(0, 255):
			self.assertEqual(i << 16, func(0, i, 0, 0))
		for i in xrange(0, 255):
			self.assertEqual(i << 24, func(i, 0, 0, 0))
		self.assertRaises(Exception, func, 0, 0, 0, 256)
		self.assertRaises(Exception, func, 0, 0, 256, 0)
		self.assertRaises(Exception, func, 0, 256,0 , 0)
		self.assertRaises(Exception, func, 256, 0, 0, 0)

	def test_ip4_to_int32(self):
		self._test4(netlib.ip4_to_int32)

	def test_ip4str_to_int32(self):
		self._test4(lambda a, b, c, d: netlib.ip4str_to_int32("%i.%i.%i.%i" % (a, b, c, d)))

	def test_ip4(self):
		self._test4(lambda a, b, c, d: int(netlib.Ip4(a, b, c, d)))
		self._test4(lambda a, b, c, d: int(netlib.Ip4("%i.%i.%i.%i" % (a, b, c, d))))

	def test_subnet_iter(self):
		n = netlib.Subnet("172.16.42.0/30")
		self.assertEqual(tuple(n), (
			netlib.Ip4(172, 16, 42, 0),
			netlib.Ip4(172, 16, 42, 1),
			netlib.Ip4(172, 16, 42, 2),
			netlib.Ip4(172, 16, 42, 3),
		))

	def test_subnet_size(self):
		n = netlib.Subnet("192.0.2.0/24")
		self.assertEqual(len(n), 256)

	def test_subnet_split(self):
		n = netlib.Subnet("192.168.1.0/24")
		self.assertEqual(n.split(8), (
			netlib.Subnet("192.168.1.0/27"),
			netlib.Subnet("192.168.1.32/27"),
			netlib.Subnet("192.168.1.64/27"),
			netlib.Subnet("192.168.1.96/27"),
			netlib.Subnet("192.168.1.128/27"),
			netlib.Subnet("192.168.1.160/27"),
			netlib.Subnet("192.168.1.192/27"),
			netlib.Subnet("192.168.1.224/27"),
		))

	def test_range_iter(self):
		r = netlib.Range("172.16.42.0", "172.16.42.3")
		self.assertEqual(tuple(r), (
			netlib.Ip4(172, 16, 42, 0),
			netlib.Ip4(172, 16, 42, 1),
			netlib.Ip4(172, 16, 42, 2),
			netlib.Ip4(172, 16, 42, 3),
		))

	def test_ip4_lt(self):
		self.assertLess(netlib.Ip4("10.41.128.1"), netlib.Ip4("10.41.191.254"))

	def test_range_len(self):
		r = netlib.Range("172.16.42.0", "172.16.42.3")
		self.assertEqual(len(r), 4)

	def test_range_index(self):
		r = netlib.Range("172.16.42.0", "172.16.42.3")
		for idx, item in enumerate(r):
			self.assertEqual(r.index(item), idx)

if __name__ == "__main__": unittest.main(verbosity = 2)
