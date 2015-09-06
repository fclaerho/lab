# copyright (c) 2015 fclaerhout.fr, released under the MIT license.

import unittest

import vagrant # 3rd-party

DEFAULT_BRIDGE = "en0: Wi-Fi (AirPort)" # Macbook + WiFi

class SelfTest(unittest.TestCase):

	def setUp(self):
		vagrant.run("mkdir -p /tmp/vgtest")
		self.guest = vagrant.Guest("/tmp/vgtest/foo")
		self.guest.init(
			box_name = "wheezy64",
			bridge = os.getenv("BRIDGE", DEFAULT_BRIDGE))

	def tearDown(self):
		self.guest.fini()
		vagrant.run("rm -rf /tmp/vgtest")

	def test_up_destroy(self):
		self.guest.up()
		try:
			assert self.guest.is_running()
		finally:
			self.guest.destroy()

	def test_double_init(self):
		self.assertRaises(
			Exception,
			self.guest.init,
			box_name = "wheezy64",
			bridge = os.getenv("BRIDGE", DEFAULT_BRIDGE))

if __name__ == "__main__": unittest.main(verbosity = 2)
