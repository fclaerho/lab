# copyright (c) fclaerhout.fr, released under the MIT license.

"""
Uninstall a packages and its unused dependencies.

Usage:
  pip-autoremove [options] NAMES...
  pip-autoremove --help

Options:
  -d, --dry-run  do not uninstall anything
  -v, --verbose  trace execution
  -h, --help     display full help text
  --no-color     disable colored output
"""

import docopt, utils, pip # 3rd-party

class Error(utils.Error): pass

# distribution attributes:
# - .project_name
# - .version
# - .location
# - .requires()
def get_distribution(name):
	for dist in pip.get_installed_distributions():
		if dist.project_name.lower() == name.lower():
			return dist
	else:
		raise Error(name, "no such distribution")

def required(dist):
	"opposite of dist.requires(): list distributions requiring dist"
	for other in pip.get_installed_distributions():
		for req in other.requires():
			if req.project_name.lower() == dist.project_name.lower():
				yield other.project_name

def uninstall(name, dryrun = True):
	utils.trace("uninstall", name)
	if not dryrun:
		pip.main(["uninstall", name])

def main(args = None):
	opts = docopt.docopt(
		doc = __doc__,
		argv = args)
	try:
		if opts["--no-color"]:
			utils.disable_colors()
		if opts["--verbose"]:
			utils.enable_tracing()
		for name in opts["NAMES"]:
			dist = get_distribution(name)
			for name in required(dist):
				raise Error(dist.project_name, "required by", name)
			for req in dist.requires():
				names = filter(lambda name: name != dist.project_name, required(req))
				if not names:
					uninstall(req.project_name, dryrun = opts["--dry-run"])
				else:
					utils.trace(req.project_name, "not uninstalled, used by", names)
			uninstall(dist.project_name, dryrun = opts["--dry-run"])
#		else:
#			for dist in pip.get_installed_distributions():
#				print utils.magenta(dist.project_name), dist.location
	except utils.Error as exc:
		raise SystemExit(utils.red(exc))

if __name__ == "__main__": main()
