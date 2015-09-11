# copyright (c) 2014-2015 fclaerhout.fr, released under the MIT license.

def strtree(
	iterable,
	maxlen = 80,
	use_ascii = False,
	is_pre_prunable = lambda it: False,
	is_post_prunable = lambda it: False):
	"""
	Return iterable as a pretty tree string.
	  * uses utf8 lines by default, set $use_ascii if your terminal has not UCS support
	  * lines are cut at $maxlen characters
	  * nodes satisfying $is_pre_prunable are pruned without being walked
	  * nodes satisfying $is_post_prunable are pruned if empty after the walk
	"""
	subprefix = "|  " if use_ascii else unicode("│  ", "utf-8")
	midprefix = "+-- " if use_ascii else unicode("├─ ", "utf-8")
	lastprefix = "`-- " if use_ascii else unicode("└─ ", "utf-8")
	def _lookahead(iterable):
		"""
		On each iteration, return the pair (element, is_last).
		Reference: http://stackoverflow.com/a/1630350
		"""
		it = iter(iterable)
		last = it.next()
		for val in it:
			yield last, False
			last = val
		yield last, True
	def _truncline(string):
		"truncate line if too long"
		if len(string) > maxlen:
			suffix = "..." if use_ascii else unicode("…", "utf-8")
			return "%s%s" % (string[:maxlen - len(suffix)], suffix)
		else:
			return string
	def _get_lines(iterable):
		"return list of lines properly prefixed"
		if is_pre_prunable(iterable):
			return []
		else:
			lines = ["%s" % iterable]
			cnt = 0
			for child, is_last_child in _lookahead(iterable):
				prefix = lastprefix if is_last_child else midprefix
				child_lines = _get_lines(child)
				if child_lines:
					cnt += 1
				for line, is_last_line in _lookahead(child_lines):
					if child_lines.index(line) == 0:
						lines.append("%s%s" % (prefix, line))
					elif is_last_child:
						lines.append("   %s" % line)
					else:
						lines.append("%s%s" % (subprefix, line))
			if not cnt and is_post_prunable(iterable):
				return []
			else:
				return lines
	return "\n".join(map(_truncline, _get_lines(iterable)))


def strcolalign(obj):
	"left-justify table or colon-separated cols in lines of text"
	maxwidth = []
	if isinstance(obj, str):
		rows = obj.splitlines()
		rows = map(lambda row: row.split(":"), rows)
	else:
		rows = obj
	# compute max width of each column:
	for row in rows:
		if len(maxwidth) < len(row):
			maxwidth += [0] * (len(row) - len(maxwidth))
		for i, col in enumerate(row):
			width = len(col) + 2 # add 2 spaces at least between columns
			maxwidth[i] = max(maxwidth[i], width)
	# render output:
	lines = []
	for row in rows:
		line = ""
		for i, col in enumerate(row):
			width = len(col)
			if i + 1 == len(maxwidth) or width == maxwidth[i]:
				line = "%s%s" % (line, col)
			else:
				line = "%s%s%s" % (line, col, " " * (maxwidth[i] - width))
		lines.append(line)
	return "\n".join(lines)