import sys
from threading import Lock

lock_call = Lock()
lock_proxy = Lock()

re_enter = False

try:del sys.modules['socket']
except:pass

import socket

old_bind = socket.socket.bind

def auto_bind(s,*argv,**kw):
    global lock, re_enter
    with lock_call:
        if not re_enter:
            with lock_proxy:
                re_enter = True
                addr,port = argv[0]
                print(f"{__name__}.auto_bind( {addr}:{port},**{kw})")
                runcmd =f"{sys.executable} -i -mwebsockify {addr}:{port+20000} 127.0.0.1:{port}"
                print(runcmd)
                try:
                    return old_bind(s,*argv,**kw)
                finally:
                    os.system(f'xterm -e "{runcmd}" &')
        else:
            print(f'binding {argv}')
        return old_bind(s,*argv,**kw)

socket.socket.bind = auto_bind


from websockify.websocketproxy import *
