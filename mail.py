# copyright (c) 2014-2015 fclaerhout.fr, released under the MIT license.

"""
Mailbox check framework and utility.

Usage:
  checkmail [--file PATH]
  checkmail --help

Options:
  -f PATH, --file PATH  configuration manifest [default: ~/checkmail.ini]
  -h, --help            show help

Status Code:
  number of unread mails (if <255) or 255 on error.
"""

import ConfigParser, imaplib, poplib, syslog, abc, sys, os

import docopt # 3rd-party

class MailBox(object):
	"mail box interface"

	__metaclass__ = abc.ABCMeta

	def __init__(self, name):
		self.name = name

	@abc.abstractmethod
	def count(self): pass

	def __str__(self):
		self.last_count = self.count()
		if self.last_count:
			return "%s: %s mail(s)" % (self.name, self.last_count)
		else:
			return "%s: no mail" % self.name

class Pop3Box(MailBox):

	def __init__(self, name, hostname, login, password, ssl = "yes"):
		super(Pop3Box, self).__init__(name = name)
		self.hostname = hostname
		self.login = login
		self.password = password
		self.ssl = ssl.lower() in ("yes", "true", "on", "1")

	def __getattr__(self, key):
		if key == "hdl":
			if self.ssl:
				self.hdl = poplib.POP3_SSL(host = self.hostname)
			else:
				self.hdl = poplib.POP3(host = self.hostname)
			self.hdl.user(self.login)
			self.hdl.pass_(self.password)
			return self.hdl
		raise AttributeError(key)

	def count(self, *args):
		cnt, _ = self.hdl.stat()
		return cnt

class ImapBox(MailBox):

	def __init__(self, name, hostname, login, password, ssl = "yes"):
		super(ImapBox, self).__init__(name = name)
		self.hostname = hostname
		self.login = login
		self.password = password
		self.ssl = ssl.lower() in ("yes", "true", "on", "1")

	def __getattr__(self, key):
		if key == "hdl":
			if self.ssl:
				self.hdl = imaplib.IMAP4_SSL(host = self.hostname)
			else:
				self.hdl = imaplib.IMAP4(host = self.hostname)
			self.hdl.login(self.login, self.password)
			return self.hdl
		raise AttributeError(key)

	def count(self, *args):
		_, counts = self.hdl.select()
		return int(counts[0])

class ConfigurationError(Exception): pass

def parse_mailboxes(path):
	conf = ConfigParser.ConfigParser()
	path = os.path.expanduser(path)
	assert conf.read(path), "%s: no such file or invalid content" % path
	for name in conf.sections():
		try:
			cls = None
			kwargs = {}
			for key, value in conf.items(name):
				if key == "type":
					if value == "pop3":
						cls = Pop3Box
					elif value == "imap":
						cls = ImapBox
					else:
						raise TypeError(value)
				else:
					kwargs[key] = value
			yield (cls)(name = name, **kwargs)
		except Exception as e:
			raise ConfigurationError("in [%s]: %s, %s" % (name, type(e).__name__, e))

def main(args = None):
	opts = docopt.docopt(
		doc = __doc__,
		argv = args)
	try:
		total = 0
		for mailbox in parse_mailboxes(path = opts["--file"]):
			print mailbox
			total += mailbox.last_count
		sys.exit(total)
	except (NotImplementedError, ConfigurationError, imaplib.IMAP4.error, poplib.error_proto, IOError) as e:
		raise SystemExit("** fatal error! %s" % e)
