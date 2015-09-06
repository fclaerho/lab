/*  ___           _   ___ _
 * | _ ) ___  ___| |_/ __| |_ _ _ __ _ _ __
 * | _ \/ _ \/ _ \  _\__ \  _| '_/ _` | '_ \
 * |___/\___/\___/\__|___/\__|_| \__,_| .__/ v1.2
 *                                    |_|
 *
 * Bootstrap functions for hosted C99 apps:
 * - No new types, only functions!
 * - Error'ing: [v]tracef
 * - Aborting: [v]abortf
 * - String handling:
 *   [v]str[cat]f, str{hash, copy, startswith, endswith, free, split, match}
 * - String-array handling:
 *   arr{0, free, copy, join, len, empty, first, last, shift, pop}
 * - File handling: {read, write}file
 *
 * Copyright (c) 2013-2015 fclaerhout.fr, released under the MIT license:
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

#include <stdarg.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <time.h>

#define RED(s) "\033[0;91m" s "\033[0m"
#define BLUE(s) "\033[0;94m" s "\033[0m"
#define GRAY(s) "\033[0;90m" s "\033[0m"
#define GREEN(s) "\033[0;92m" s "\033[0m"
#define YELLOW(s) "\033[0;93m" s "\033[0m"
#define PURPLE(s) "\033[0;95m" s "\033[0m"

/* return nothing, output a time-stamped formatted message to stderr.
 */
void vtracef(const char *fmt, va_list list) {
 	clock_t elapsed = clock() / CLOCKS_PER_SEC;
	time_t now = time(0);
	struct tm tm = *localtime(&now);
	char prefix[20]; /* 20 = size of expanding "%Y/%m/%d %H:%M:%S" */
	(void)strftime(prefix, sizeof(prefix), "%Y.%m.%d.%H.%M.%S", &tm);
	va_list lcpy;
	va_copy(lcpy, list);
	int len = vsnprintf(0, 0, fmt, list);
	char str[len + 1];
	(void)vsnprintf(str, len + 1, fmt, lcpy);
	va_end(lcpy);
	(void)fprintf(stderr, GRAY("%s+%lu") ": %s\n", prefix, elapsed, str);
}

/* wrap vtracef().
 */
void tracef(const char *fmt, ...) {
	va_list list;
	va_start(list, fmt);
	vtracef(fmt, list);
	va_end(list);
}

/* return nothing, abort execution and output a user-supplied explanation.
 */
void vabortf(const char *fmt, va_list list) {
	extern char *strf(const char *fmt, ...);
	char *xfmt = strf(RED("aborting") ": %s", fmt);
	extern void vtracef(const char *fmt, va_list);
	vtracef(xfmt, list);
	extern void free(void *ptr);
	free(xfmt);
	extern void abort(void);
	abort();
}

/* wrap vabortf().
 */
void abortf(const char *fmt, ...) {
	va_list list;
	va_start(list, fmt);
	vabortf(fmt, list);
	va_end(list);
}

/* sdbm classic hash.
 */
unsigned long strhash(char *str) {
	unsigned long h = 0;
	for(; *str; ++str) h = *str + (h << 6) + (h << 16) - h;
	return h;
}

/* (re)allocate heap memory or abort on shortage.
 */
void *alloc(void *p, size_t len) {
	p = p? realloc(p, len): calloc(1, len);
	if(!p) abortf("out of memory, cannot allocate %zu bytes", len);
	return p;
}

/* return an allocated C-string from the formatted input.
 */
char* vstrf(const char *fmt, va_list list) {
	va_list lcpy;
	va_copy(lcpy, list);
	int len = vsnprintf(0, 0, fmt, list);
	char *str = alloc(0, len + 1);
	(void)vsnprintf(str, len + 1, fmt, lcpy);
	va_end(lcpy);
	return str;
}

/* wrap vstrf().
 */
char* strf(const char *fmt, ...) {
	va_list list;
	va_start(list, fmt);
	char *str = vstrf(fmt, list);
	va_end(list);
	return str;
}

/* return an allocated copy of $str.
 */
char *strcopy(const char *str) {
	char *cpy = calloc(1, strlen(str) + 1);
	(void)strcpy(cpy, str);
	return cpy;
}

/* return *$str reallocated and suffixed with the formatted input.
 */
void vstrcatf(char **str, const char *fmt, va_list list) {
	va_list lcpy;
	va_copy(lcpy, list);
	size_t fmtlen = vsnprintf(0, 0, fmt, lcpy);
	va_end(lcpy);
	size_t srclen = strlen(*str);
	*str = realloc(*str, srclen + fmtlen + 1);
	(void)vsnprintf(*str + srclen, fmtlen + 1, fmt, list);
}

/* wrap vstrcatf().
 */
void strcatf(char **str, const char *fmt, ...) {
	va_list list;
	va_start(list, fmt);
	vstrcatf(str, fmt, list);
	va_end(list);
}

/* return true if $str starts with $prefix.
 */
_Bool strstartswith(const char *str, const char *prefix) {
	for(; *prefix && *str && *prefix == *str; ++prefix, ++str);
	return !*prefix;
}

/* return true if $str ends with $suffix.
 */
_Bool strendswith(const char *str, const char *suffix) {
	unsigned srclen = strlen(str);
	unsigned suflen = strlen(suffix);
	for(; suflen && srclen && suffix[suflen] == str[srclen]; --suflen, --srclen);
	return !suflen;
}

/* return an allocated nul-terminated array of C-strings from the given elements.
 * the last argument must be \0.
 */
char** arr0(char *str, .../*, 0 */) {
	va_list list;
	va_start(list, str);
	size_t len = 0;
	for(; str; str = va_arg(list, char *)) ++len;
	char **arr = alloc(0, sizeof(char *) * (len + 1));
	va_start(list, str);
	for(size_t i = 0; str; str = va_arg(list, char *)) arr[i++] = str;
	va_end(list);
	arr[len] = 0;
	return arr;
}

/* return the concatenation of the strings in @arr, separated by $sep.
 */
char* arrjoin(char **arr, const char *sep) {
	size_t len = 0;
	for(char **cur = arr; *cur; ++cur) len += strlen(*cur) + 1; /* sep or \0 */
	char *str = alloc(0, len);
	for(char **cur = arr; *cur; ++cur) {
		if(cur > arr) (void)strcat(str, sep);
		(void)strcat(str, *cur);
	}
	return str;
}

/* return the number of strings in @arr (excluding the terminating \0).
 */
size_t arrlen(char **arr) {
	size_t len = 0;
	for(; *arr; ++arr) ++len;
	return len;
}

/* return a copy of @arr.
 */
char **arrcopy(char **arr) {
	size_t len = arrlen(arr);
	char **cpy = alloc(0, (len + 1) * sizeof(char*));
	for(size_t i = 0; i < len; ++i) cpy[i] = strcopy(arr[i]);
	return cpy;
}

/* return true if @arr is empty (i.e. equal to {0}).
 */
_Bool arrempty(char **arr) { return !arr[0]; }

/* return the first string in @arr.
 */
const char *arrfirst(char **arr) {
	if(arrempty(arr)) abortf("%s(): empty array", __func__);
	return arr[0];
}

/* return the last string in @arr.
 */
const char *arrlast(char **arr) {
	if(arrempty(arr)) abortf("%s(): empty array", __func__);
	return arr[arrlen(arr) - 1];
}

/* return the first string of *@arr and remove it;
 * release and unset *@arr if it's empty.
 */
char *arrshift(char ***arr) {
	char *str = (char*)arrfirst(*arr);
	unsigned len = arrlen(*arr);
	for(unsigned i = 0; i < len; ++i) (*arr)[i] = (*arr)[i + 1];
	if(len <= 1) { /* empty array */
		free(*arr);
		*arr = 0;
	}
	return str;
}

/* return the last string of *@arr and remove it;
 * release and unset *@arr if it's empty.
 */
char *arrpop(char ***arr) {
	char *str = (char*)arrlast(*arr);
	unsigned len = arrlen(*arr);
	(*arr)[len - 1] = 0;
	if(len <= 1) { /* empty array */
		free(*arr);
		*arr = 0;
	}
	return str;
}

/* apply mapper to each of *@arr string elements.
 */
void arrmap(char **arr, char *(*map)(char*)) {
	for(; *arr; ++arr) *arr = map(*arr);
}

/* return an allocated nul-terminated array of allocated
 * C-strings by splitting $str on each $sep.
 */
char** strsplit(const char *str, const char *sep) {
	char **arr = 0;
	size_t cnt = 0;
	const char *head = str;
	const char *tail = str;
	for(;;) {
		if(!*tail || strstr(tail, sep) == tail) { /* push [head:tail] */
			arr = alloc(arr, (cnt + 1) * sizeof(char*));
			char *sub = calloc(1, tail - head);
			(void)strncpy(sub, head, tail - head);
			arr[cnt] = sub;
			++cnt;
			if(!*tail) break;
			tail += strlen(sep);
			head = tail;
		} else ++tail;
	}
	arr = alloc(arr, (cnt + 1) * sizeof(char*));
	arr[cnt] = 0;
	return arr;
}

/* return (_Bool)1 if $str matches $glob, (_Bool)0 otherwise.
 * supported meta-characters: * and ?
 */
_Bool strmatch(const char *str, const char *glob) {
	for(; *glob && *str; ++str) {
		switch(*glob) {
			case '*':
				if(*(glob + 1) == *(str + 1)) ++glob;
				break;
			case '?':
				++glob;
				break;
			default:
				if(*glob != *str) return 0;
				++glob;
		}
	}
	return !*str && (!*glob || (*glob == '*' && !*(glob + 1)));
}

/* return an allocated C-string read from the file content.
 */
char* readfile(const char *name) {
	FILE *f = fopen(name, "r");
	if(!f) abortf("%s(): fopen(%s) failed: %s", __func__, name, strerror(errno));
	if(fseek(f, 0, SEEK_END) == -1) abortf("%s(): fseek(%s) failed: %s", __func__, name, strerror(errno));
	long len = ftell(f);
	if(len == -1) abortf("%s(): cannot ftell(%s): %s", __func__, name, strerror(errno));
	rewind(f);
	char *buf = calloc(1, len + 1);
	if(!buf) abortf("%s(): out of memory", __func__);
	if(fread(buf, len, 1, f) != 1) abortf("%s(): fread(%s) failed: %s", __func__, name, strerror(errno));
	if(fclose(f)) abortf("%s(): fclose(%s) failed: %s", __func__, name, strerror(errno));
	return buf;
}

/* return nothing, write $str to the file.
 */
void writefile(const char *name, const char *str) {
	FILE *f = fopen(name, "w+");
	if(!f) abortf("%s(): fopen(%s) failed: %s", __func__, name, strerror(errno));
	if(fwrite(str, strlen(str), 1, f) != 1) abortf("%s(): fwrite(%s) failed: %s", __func__, name, strerror(errno));
	if(fclose(f)) abortf("%s(): fclose(%s) failed: %s", __func__, name, strerror(errno));
}

#if defined(NIX)

	#include <sys/types.h>
	#include <sys/wait.h>
	#include <assert.h>
	#include <unistd.h>

	static inline int exec(char *in, char **out, char **err, int argc, char **argv) {
		int ifd[2];
		int ofd[2];
		int efd[2];
		if(in && pipe(ifd) == -1) abortf("pipe() for in failed");
		if(out && pipe(ofd) == -1) abortf("pipe() for out failed");
		if(err && pipe(efd) == -1) abortf("pipe() for err failed");
		switch(fork()) {
			case -1:
				abortf("fork() failed");
			case 0: /* child process */
				if(in) {
					assert(close(ifd[1]) != -1); /* close unused fd */
					assert(dup2(ifd[0], 0) != -1); /* reset stdin */
				}
				if(out) {
					assert(close(ofd[0]) != -1); /* close unused fd */
					assert(dup2(ofd[1], 1) != -1); /* reset stdout */
				}
				if(err) {
					assert(close(efd[0]) != -1); /* close unused fd */
					assert(dup2(efd[1], 2) != -1); /* reset stderr */
				}
				assert(execvp(*argv, argv) != -1);
			default: { /* parent process */
				if(in) {
					assert(close(ifd[0]) != -1); /* close unused fd */
					for(;;) {
						int len = write(ifd[1], in, strlen(in));
						if(len <= 0) break;
						in += len;
					}
					assert(close(ifd[1]) != - 1);
				}
				if(out) {
					assert(close(ofd[1]) != -1); /* close unused fd */
					*out = strf("");
					for(;;) {
						char buf[512] = {};
						int len = read(ofd[0], buf, sizeof(buf));
						if(len <= 0) break;
						strcatf(out, "%s", buf);
					}
					assert(close(ofd[0]) != -1);
				}
				if(err) {
					assert(close(efd[1]) != -1); /* close unused fd */
					*err = strf("");
					for(;;) {
						char buf[512] = {};
						int len = read(efd[0], buf, sizeof(buf));
						if(len <= 0) break;
						strcatf(err, "%s", buf);
					}
					assert(close(efd[0]) != -1);
				}
				int res;
				(void)wait(&res);
				if(WIFEXITED(res)) return WEXITSTATUS(res);
			}
		}
		return EXIT_FAILURE;
	}

	int vcmdf(char *in, char **out, char **err, char *fmt, va_list list) {
		char *str = vstrf(fmt, list);
		char **arr = strsplit(str, " "); /* FIXME: shell expr parse */
		int res = exec(in, out, err, arrlen(arr), arr);
		arrfree(&arr);
		strfree(&str);
		return res;
	}

#elif defined(WIN)

	#error not yet supported

#elif defined(FALLBACK)

	int vcmdf(char *in, char **out, char **err, const char *fmt, va_list list) {
		char *ename = 0;
		char *oname = 0;
		char *cmd = vstrf(fmt, list);
		if(in) {
			abortf("unsupported feature: in redirection");
		}
		if(err) {
			ename = alloc(0, L_tmpnam);
			if(!tmpnam(ename)) abortf("%s(): tmpnam() failed: %s", __func__, strerror(errno));
			strcatf(&cmd, " 2>%s", ename);
		}
		if(out) {
			oname = calloc(0, L_tmpnam);
			if(!tmpnam(oname)) abortf("%s(): tmpnam() failed: %s", __func__, strerror(errno));
			strcatf(&cmd, " >%s", oname);
		}
		int ret = system(cmd);
		if(ret == -1 || ret == 127) abortf("%s(): system(%s) failed: %s", __func__, cmd, strerror(errno));
		free(cmd);
		if(err) {
			*err = readfile(ename);
			remove(ename);
			free(ename);
		}
		if(out) {
			*out = readfile(oname);
			remove(oname);
			free(oname);
		}
		return ret;
	}
int cmdf(char *in, char **out, char **err, char *fmt, ...) {
	va_list list;
	va_start(list, fmt);
	int res = vcmdf(in, out, err, fmt, list);
	va_end(list);
	return res;
}

#endif
