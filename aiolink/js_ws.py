

import asyncio
import json

from . import *

class JSProxy(Proxy):

    def __init__(self):
        self.caller_id = 0
        self.tmout = 300
        self.cache = {}
        self.q_return = {}
        self.q_sync = []
        self.q_async = []

    def new_call(self):
        self.caller_id += 1
        return str(self.caller_id)

    async def wait_answer(self,cid, fqn, solvepath):
        #cid = str(self.caller_id)
        if DBG:print('\tas id %s' % cid)
        unsolved = fqn[len(solvepath)+1:]
        tmout = self.tmout
        if DBG and unsolved:
            print('\twill remain', unsolved )
        solved = None

        while tmout>0:
            if cid in self.q_return:
                oid, solved = self.unref(cid)
                if len(unsolved):
                    solved = await self.get( "%s.%s" % ( oid, unsolved ) , None )
                    unsolved = ''
                    break
                break
            await aio.asleep_ms(1)
            tmout -= 1
        return solved, unsolved


    def unref(self, cid):
        oid = self.q_return.pop(cid)
        tip="%s@%s"%( oid,cid )
        if isinstance(oid,str) and oid.startswith('js|'):
            if oid.find('/')>0:
                oid,tip = oid.split('/',1)
        if not oid in self.cache:
           self.cache[oid] = CallPath(None,oid,tip=tip)
        return oid, self.cache[oid]

    async def get(self, cp,argv,**kw):
        print('async_js_get',cp,argv)
        cid = self.new_call()
        self.q_async.append( {"id": cid, 'm':cp } )

        while True:
            if cid in self.q_return:
                return self.q_return.pop(cid)
            await aio.asleep_ms(1)

    def set(self, cp,argv,cs=None):
        if cs is not None:
            if len(cs)>1:
                raise Exception('please simplify assign via (await %s(...)).%s = %r' % (cs[0][0], name,argv))
            value = argv
            solvepath, argv, kw = cs.pop(0)
            unsolved = cp[len(solvepath)+1:]

            jsdata = f"JSON.parse(`{json.dumps(argv)}`)"
            target = solvepath.rsplit('.',1)[0]
            assign = f'JSON.parse(`{json.dumps(value)}`)'
            doit = f"{solvepath}.apply({target},{jsdata}).{unsolved} = {assign}"
            print("74:",doit)
            return self.q_sync.append(doit)

        if cp.count('|'):
            cp  = cp.split('.')
            cp[0] = f'window["{cp[0]}"]'
            cp = '.'.join( cp )

        if DBG:
            print('82: set',cp,argv)
        self.q_sync.append( f'{cp} =  JSON.parse(`{json.dumps(argv)}`)' )

    def act(self, cp,c_argv,c_kw,**kw):
        cid = self.new_call()
        self.q_async.append( {"m": cp, "a": c_argv, "k": c_kw, "id": cid} )
        return cid


CallPath.set_proxy(JSProxy())


class JsServer(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('connection from {}'.format(peername))
        self.transport = transport
        #data = open('/srv/www/html/terms/miedit-master/dump','rb').read()
        data = b"3613 PYTHON37"
        self.transport.write(data  )

    def data_received(self, data):

        try:
            data =  data.decode().strip("\r\n")[1:]
            # close the socket
            if data.count( chr(4) ):
                print('EOF')
                self.transport.close()
                return
            data = json.loads(data)

            while len(data):
                k,v=data.popitem()
                CallPath.proxy.q_return[k]=v
                if DBG:print('response {} = [{}]'.format( k,v) )

            if len(CallPath.proxy.q_sync):
                self.transport.write(bytes( f"//S:{CallPath.proxy.q_sync.pop(0)}\r\n", 'utf-8') )
            elif len(CallPath.proxy.q_async):
                self.transport.write(bytes( f"//A:{json.dumps(CallPath.proxy.q_async.pop(0))}\r\n", 'utf-8') )
            else:
                self.transport.write(b"//YOU ! AGAIN ?\r\n")

        except Exception as e:
            print(e)

