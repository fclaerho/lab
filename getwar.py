def download_war(
	baseurl,
	groupid,
	name,
	version = None,
	suffix = None,
	is_snapshot = False,
	is_tomcat_webapp = True):
	"""
	Download the war of a given project from an artifactory repository.
	If no $version is specified, the latest will be used.
	If the war is to be deployed on a tomcat server, set $is_tomcat_webapp.
	"""
	def check_urlopen(url):
		fp = urllib.urlopen(url)
		if fp.getcode() != 200:
			raise IOError("%s: http error %i" % (url, fp.getcode()))
		else:
			return fp
	url = "/" .join((baseurl, groupid.replace(".", "/"), name, "maven-metadata.xml"))
	if not version:
		# find latest version:
		fp = check_urlopen(url)
		root = XML.fromstring(fp.read())
		version = root.find("./versioning/latest").text
	if is_snapshot:
		# get exact timestamped version for a snapshot:
		url = "/" .join((baseurl, groupid.replace(".", "/"), name, version, "maven-metadata.xml"))
		fp = check_urlopen(url)
		root = XML.fromstring(fp.read())
		tsversion = root.find("./version").text
		warname = "-".join(filter(None, (name, tsversion, suffix))) + ".war"
	else:
		warname = "-".join(filter(None, (name, version, suffix))) + ".war"
	url = "/" .join((baseurl, groupid.replace(".", "/"), name, latest, warname))
	basename = "%s##%s.war" % (name, version) if is_tomcat_webapp else warname
	print "downloading", basename, "..."
	fp_in = check_urlopen(url)
	with open(basename, "wb") as fp_out:
		shutil.copyfileobj(fp_in, fp_out)
	print "ok"
