/* copyright (c) 2009-2010 fclaerhout.fr, licensed under the GPL3
   library-independent c program template v20091006
   $ cc -fno-builtin -nostdlib -s nolib_linux_ia32.c -o foo
   use /usr/include/asm/unistd.h for syscall list
   use /usr/include/asm-generic/errno-base.h for errno list */

/* THIS IS JUST AN EXPERIMENT -- DO NOT USE */

/* Cast helpers.
 */
#define DUS(i) *(unsigned short*)(i)
#define DB(i)  *(unsigned char*)(i)
#define DI(i)  *(int*)(i)

/* cc expects _start to be called but it is jumped to;
 * env vars and command line args are pushed onto the stack.
 */
_start(argv0) { start(DI(&argv0-1),&argv0,&argv0+DI(&argv0-1)+1); }

itos(i,b) { /* convert int to char* in base 2<b<=16 */
 static char s[16]={0};
 int x=14,y=i<0,z=y?-i:i;
 do { s[x]="0123456789abcdef"[z%b]; --x; z/=b; } while(z && x);
 if(x && y) s[x--]='-';
 return (int)(s+x+1);
}

slen(s) { int i; for(i=0;DB(s);++i,++s); return i; }

call(a,b,c,d) { /* do syscall */
 asm("movl %0,%%eax;"
     "movl %1,%%ebx;"
     "movl %2,%%ecx;"
     "movl %3,%%edx;"
     "int $0x80;"::"g"(a),"g"(b),"g"(c),"g"(d)); /* return %eax */
}

char unam[390]; /* struct utsname */
char sinf[64];  /* struct sysinfo */
char stat[88];  /* struct stat */
char rlim[8];   /* struct rlimit */
char utim[8];   /* struct utime */
char tspe[8];   /* struct timespec */
char cwd[256];  /* PATH_MAX=256 */
int tmp;

char sigaction[140];
char cpuset[128];

char tms[16];

/* return (int) or (char*) */
#define bufferram        (call(116,sinf,0,0)>=0?DI(sinf+28)*DI(sinf+52):0)
#define chrt_p(p)        call(157,p,0,0)/*0:other 1:fifo 2:rr 3:batch*/
#define date             call(13,0,0,0)
#define egid             call(50,0,0,0)
#define euid             call(49,0,0,0)
#define freehigh         (call(116,sinf,0,0)>=0?DI(sinf+48)*DI(sinf+52):0)
#define freeswap         (call(116,sinf,0,0)>=0?DI(sinf+36)*DI(sinf+52):0)
#define freeram          (call(116,sinf,0,0)>=0?DI(sinf+20)*DI(sinf+52):0)
#define gid              call(47,0,0,0)
#define loads1           (call(116,sinf,0,0)>=0?DI(sinf+4):0)
#define loads5           (call(116,sinf,0,0)>=0?DI(sinf+8):0)
#define loads15          (call(116,sinf,0,0)>=0?DI(sinf+12):0)
#define pid              call(20,0,0,0)
#define ppid             call(64,0,0,0)
#define procs            (call(116,sinf,0,0)>=0?DUS(sinf+40):0)
#define pwd              (call(183,cwd,sizeof(cwd),0)>=0?cwd:".")
#define sharedram        (call(116,sinf,0,0)>=0?DI(sinf+24)*DI(sinf+52):0)
#define stat_cd(f)       (call(106,f,stat,0)>=0?DI(stat):0)
#define stat_ci(f)       (call(106,f,stat,0)>=0?DI(stat+4):0)
#define stat_cf(f)       (call(106,f,stat,0)>=0?DUS(stat+8):0)
#define stat_ch(f)       (call(106,f,stat,0)>=0?DB(stat+10):0)
#define stat_cu(f)       (call(106,f,stat,0)>=0?DUS(stat+12):0)
#define stat_cg(f)       (call(106,f,stat,0)>=0?DUS(stat+14):0)
#define stat_ct(f)       (call(106,f,stat,0)>=0?DB(stat+17):0)
#define stat_cT(f)       (call(106,f,stat,0)>=0?DB(stat+16):0)
#define stat_cs(f)       (call(106,f,stat,0)>=0?DI(stat+20):0)
#define stat_co(f)       (call(106,f,stat,0)>=0?DI(stat+24):0)
#define stat_cb(f)       (call(106,f,stat,0)>=0?DI(stat+28):0)
#define stat_cX(f)       (call(,106,f,stat,0)>=0?DI(stat+32):0)
#define stat_cY(f)       (call(106,f,stat,0)>=0?DI(stat+40):0)
#define stat_cZ(f)       (call(106,f,stat,0)>=0?DI(stat+48):0)
#define totalhigh        (call(116,sinf,0,0)>=0?DI(sinf+44)*DI(sinf+52):0)
#define totalram         (call(116,sinf,0,0)>=0?DI(sinf+16)*DI(sinf+52):0)
#define totalswap        (call(116,sinf,0,0)>=0?DI(sinf+32)*DI(sinf+52):0)
#define uid              call(24,0,0,0)
#define ulimit(i)        (call(76,i,rlim,0)>=0?DI(rlim):0)
#define ulimit_c         ulimit(4)
#define ulimit_d         ulimit(2)
#define ulimit_e         ulimit(13)
#define ulimit_f         ulimit(1)
#define ulimit_i         ulimit(11)
#define ulimit_l         ulimit(8)
#define ulimit_m         ulimit(5)
#define ulimit_n         ulimit(7)
#define ulimit_p         -
#define ulimit_q         ulimit(12)
#define ulimit_r         ulimit(14)
#define ulimit_s         ulimit(3)
#define ulimit_t         ulimit(0)
#define ulimit_u         ulimit(6)
#define ulimit_v         ulimit(9)
#define ulimit_x         ulimit(10)
#define uname_s          (call(122,unam,0,0)>=0?unam:"")
#define uname_n          (call(122,unam,0,0)>=0?unam+65:"")
#define uname_r          (call(122,unam,0,0)>=0?unam+2*65:"")
#define uname_v          (call(122,unam,0,0)>=0?unam+3*65:"")
#define uname_m          (call(122,unam,0,0)>=0?unam+4*65:"")
#define uptime           (call(116,sinf,0,0)>=0?DI(sinf):0)
#define wait(p)          ((call(7,p,&tmp,0)>=0\
                          && (tmp&0x7f)==0)?((tmp&0xff00)>>8):0)

/* return 0 (on failure) or 1 (on success) */
#define append(s,f)      -
#define arp()            -
#define cd(f)            (call(12,f,0,0)>=0)
#define chgrp(f,i)       (call(16,f,-1,i)>=0)
#define chmod(f,i)       (call(15,f,i,0)>=0)
#define chown(f,i)       (call(16,f,i,-1)>=0)
#define chroot(f)        (call(61,f,0,0)>=0)
#define chrt_pb(i,p)     (tmp=i,call(156,p,3,&tmp)>=0)
#define chrt_pf(i,p)     (tmp=i,call(156,p,1,&tmp)>=0)
#define chrt_po(i,p)     (tmp=i,call(156,p,0,&tmp)>=0)
#define chrt_pr(i,p)     (tmp=i,call(156,p,2,&tmp)>=0)
#define date_s(i)        (call(25,i,0,0)>=0)
#define echo(s)          (echo_n(s),echo_n("\n")) /* FIXME */
#define echo_n(s)        (tmp=(int)s,call(4,1,tmp,slen(tmp))>=0)
#define exec(f,a,e)      (call(11,f,a,e)>=0)
#define exit(i)          (call(1,i&0xff,0,0),1)
#define getconf(s)       -
#define halt_fn          (call(88,0xfee1dead,672274793,0xcdef0123)>=0)
#define hwclock()        -
#define ifconfig()       -
#define ifdown()         -
#define ifup()           -
#define insmod(s)        -
#define kill(p)          kill_s(p,15)
#define kill_s(p,i)      (call(37,p,i,0)>=0)
#define ln(f,f2)         (call(9,f,f2,0)>=0)
#define ln_s(f,f2)       (call(83,f,f2,0)>=0)
#define logger(s)        -
#define lsmod(h)         -
#define mkdir(f)         (call(39,f,0,0)>=0)
#define mknod_b(f,i,j)   (call(14,f,060666,i<<8|(j&0xff))>=0)
#define mknod_c(f,i,j)   (call(14,f,020666,i<<8|(j&0xff))>=0)
#define mkfifo(f)        (call(14,f,010666,0)>=0)
#define mount(s,f,t,v)   -
#define mv(f,f2)         (call(38,f,f2,0)>=0)
#define nice(i,h)        ((call(2,0,0,0)==0) &&\
                          ((call(34,i,0,0)>=0 & h())?exit(0):exit(1)))
#define poweroff_fn      (call(88,0xfee1dead,672274793,0x4321fedc)>=0)
#define reboot_fn        (call(88,0xfee1dead,672274793,0x1234567)>=0)
#define route(h)         -
#define rm(f)            (call(10,f,0,0)>=0)
#define rmdir(f)         (call(40,f,0,0)>=0)
#define rmmod(s)         -
#define sleep(i)         (DI(tspe)=i,call(162,tspe,tspe,0)>=0)
#define stty()           -
#define suspend          kill_s(pid,19)
#define swapoff(f)       (call(115,f,0,0)>=0)
#define swapon(f)        (call(87,f,0,0)>=0)
#define sync             (call(36,0,0,0),1)
#define sysctl()         -
#define taskset_p(i,p)   - (_mset(cpuset,0,sizeof(cpuset),\
                          /*fixme*/_bset(cpuset,i),\
                          call("!taskset/sched_setaffinity",241,p,\
                           sizeof(cpuset),cpuset)>=0)
#define test_r(f)        (call(33,f,4,0)>=0)
#define test_w(f)        (call(33,f,2,0)>=0)
#define test_x(f)        (call(33,f,1,0)>=0)
#define test_e(f)        (call(33,f,0,0)>=0)
#define test_b(f)        (stat_f(f)&0060000)
#define test_c(f)        (stat_f(f)&0020000)
#define test_d(f)        (stat_f(f)&0040000)
#define test_f(f)        (stat_f(f)&0100000)
#define test_l(f)        (stat_f(f)&0120000)
#define test_p(f)        (stat_f(f)&0010000)
#define test_s(f)        (stat_f(f)&0140000)
#define test_o(f)        (stat_u(f)==euid)
#define test_g(f)        (stat_f(f)&0002000)
#define test_u(f)        (stat_f(f)&0004000)
#define test_et(f,f2)    (stat_d(f)==stat_d(f2) && stat_i(f)==stat_i(f2))
#define test_nt(f,f2)    (stat_y(f)>stat_y(f2))
#define test_ot(f,f2)    (stat_y(f)<stat_y(f2))
#define touch(f)         (test_e(f)?call(30,f,0,0):call(14,f,0100666,0))
#define touch_d(f,i,j)   (test_e(f)?\
                          (DI(utim)=i,DI(utim+4)=j,call(30,f,utim,0)):\
                          call(14,f,0100666,0))
#define trap(h,i)        (DI(sigaction)=(int)h,DI(sigaction+4)=-1/*mask all*/,\
                          DI(sigaction+...)=0,call(67,i,sigaction,0)>=0)
#define ulimit_SH(i,j,k) (DI(rlim)=i,DI(rlim+4)=j,call(75,k,rlim,0)>=0)
#define ulimit_SHc(i,j)  ulimit_SH(i,j,4)
#define ulimit_SHd(i,j)  ulimit_SH(i,j,2)
#define ulimit_SHe(i,j)  ulimit_SH(i,j,13)
#define ulimit_SHf(i,j)  ulimit_SH(i,j,1)
#define ulimit_SHi(i,j)  ulimit_SH(i,j,11)
#define ulimit_SHl(i,j)  ulimit_SH(i,j,8)
#define ulimit_SHm(i,j)  ulimit_SH(i,j,5)
#define ulimit_SHn(i,j)  ulimit_SH(i,j,7)
#define ulimit_SHp(i,j)  -
#define ulimit_SHq(i,j)  ulimit_SH(i,j,12)
#define ulimit_SHr(i,j)  ulimit_SH(i,j,14)
#define ulimit_SHs(i,j)  ulimit_SH(i,j,3)
#define ulimit_SHt(i,j)  ulimit_SH(i,j,0)
#define ulimit_SHu(i,j)  ulimit_SH(i,j,6)
#define ulimit_SHv(i,j)  ulimit_SH(i,j,9)
#define ulimit_SHx(i,j)  ulimit_SH(i,j,10)
#define umask(i)         (call(60,i,0,0),1)
#define umount(s)        (call(22,s,0,0)>=0)

/* usage example */
start(argc,argv,envp) {
 echo("test");
 kill_s(1,9) || echo("failed");
 (chrt_pr(99,pid) && echo("ok")) || echo("argh");
 char* a[]={"/bin/ls","-a",0};
 exec("/bin/ls",a,0) && echo("ok");
 exit(0);
}
