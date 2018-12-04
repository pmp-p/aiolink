DBG = 1

class pe_str(str):
    def __call__(self, *argv, **kw):
        if Proxy.act:
            Proxy.act(self.fqn, argv, kw)
        else:
            pdb(f"6:pe__call__ {self.fqn}({argv},{kw})")

    async def __solver(self):
#use old value as default ?
        print('pe-solve',self.fqn)
        return await CallPath.proxy.get( self.fqn , None )

    def __await__(self):
        print('pe-await',self.fqn)
        return self.__solver().__await__()

PE = dict()
PE["str"] = pe_str


#class PathEnd(object):
#    def __init__(self, host, fqn, default=None):
#        self.__fqn = fqn
#        self.__name = fqn.rsplit(".", 1)[-1]
#        self.__host = host
#        self.__host._cp_setup(self.__name, default)
#
#    def __get__(self, obj, objtype):
#        rv = self.__host[self.__name]
#        rv = PE.get(type(rv).__name__, pe_str)(rv)
#        rv.fqn = self.__fqn
#        if DBG:
#            print("27:pe-get", self.__fqn, "==", repr(rv))
#        if Proxy.get:
#            Proxy.get(self.__fqn, rv, **Proxy.cfg.get("get", {}))
#        return rv
#
#    def __set__(self, obj, val):
#        print("33:pe-set", self.__name)
#        self.__host[self.__name] = val

class Proxy:
#FIXME provide loopback sample

    get = None
    act = None
    set = None
    tmout = 300
    cfg = {"get": {}, "set": {}, "act": {}}

class CallPath(dict):

    proxy = Proxy



    cache = {}



    def __init__(self, host, fqn, default=None, tip='[object]'):
        self.__fqn = fqn
        self.__name = fqn.rsplit(".", 1)[-1]
        self.__host = host


        #empty call stack
        self.__cs = []
        self.__tmout = 500
        self.__tip  = tip
        if host:
            self.__host._cp_setup(self.__name, default)
        dict.__init__(self)

    @classmethod
    def set_proxy(cls,proxy):
        cls.proxy = proxy
        proxy.cp = cls
        cls.get = proxy.get
        cls.set = proxy.set
        cls.act = proxy.act


    def __getattr__(self, name):
        if name in self:
            return self[name]
        fqn = "%s.%s" % (self.__fqn, name)
#        if DBG:
#            print("72:cp-ast", fqn)
        newattr = self.__class__(self, fqn)
        self._cp_setup(name, newattr)
        return newattr

    def __setattr__(self, name, value):
        if name.startswith("_"):
            return dict.__setattr__(self, name, value)

        fqn = "%s.%s" % (self.__fqn, name)
        if DBG:
            print("105:cp->pe", fqn, ":=", value, self.__cs)

        if len(self.__cs):
            self.proxy.set(fqn,value,self.__cs)
            self.__cs.clear()
            #can't assign path-end to a dynamic callpath
            return

#FIXME: caching type/value is flaky
        #setattr(self.__class__, name, PathEnd(self, fqn, value))
        self.proxy.set(fqn, value)

#FIXME: caching type/value is flaky
#    def __setitem__(self, name, v):
#        fqn = "%s.%s" % (self.__fqn, name)
#        setattr(self.__class__, key, PathEnd(host, fqn, default=v))

    def _cp_setup(self, key, v):
        if v is None:
            print("86:cp-set None ????", key, v)
            return

        if not isinstance(v, self.__class__):
            print("87:cp-set", key, v)
            if self.__class__.set:
                if DBG:
                    print("93:cp-set", key, v)
                self.proxy.set("%s.%s" % (self.__fqn, key), v)

        dict.__setitem__(self, key, v)


    async def __solver(self):
        cs = []
        p = self
        while p.__host:
            if p.__cs :
                cs.extend(p.__cs)
            p = p.__host
        cs.reverse()

        unsolved = self.__fqn
        cid='?'
        # FIXME: (maybe) for now just limit to only one level of call()
        # horrors like "await window.document.getElementById('test').textContent.length" are long enough already.
        if len(cs):
            solvepath, argv, kw = cs.pop(0)
            if DBG:print(self.__fqn,'about to solve', solvepath,argv,kw)
            cid = self.proxy.act(solvepath, argv, kw )
            solved, unsolved = await self.proxy.wait_answer(cid, unsolved, solvepath)
#FIXME:         #timeout: raise ? or disconnect event ?
#FIXME: strip solved part on fqn and continue in callstack
            if not len(unsolved):
                return solved
        else:
            if DBG:print('__solver about to solve',unsolved)
            return await self.proxy.get( unsolved , None )

        return 'future-async-unsolved[%s->%s]' % (cid,unsolved)

    def __await__(self):
        return self.__solver().__await__()

    def __call__(self, *argv, **kw):
        if DBG:
            print("89:cp-call", self.__fqn, argv, kw)
        #stack up the async call list
        self.__cs.append( [self.__fqn, argv, kw ] )
        return self


# maybe yield from https://stackoverflow.com/questions/33409888/how-can-i-await-inside-future-like-objects-await
#        async def __call__(self, *argv, **kw):
#
#            self.__class__.act(self.__fqn, argv, kw)
#            cid  = str( self.__class__.caller_id )
#            rv = ":async-cp-call:%s" % cid
#            while True:
#                if cid in self.q_return:
#                    oid = self.q_return.pop(cid)
#                    if oid in self.cache:
#                        return self.cache[oid]
#
#                    rv = self.__class__(None,oid)
#                    self.cache[oid]=rv
#                    break
#                await asleep_ms(1)
#            return rv

    def __repr__(self):
        if self.__fqn.count('|'):
            #print("FIXME: give tip about remote object proxy")
            return self.__tip
        raise Exception("Giving cached value from previous await %s N/I" % self.__fqn)

        #return ":async-pe-get:%s" % self.__fqn


if __name__ == "__main__":
    window = CallPath(None, "window")

    print()
    print("-" * 30)
    print(window.document.title)

    try:
        window.document.title += "gotcha!"
    except Exception as e:
        print("not yet :", e)

    print()
    print("-" * 30)
    print(window.document.title)

    print()
    print("=" * 30)
    window.document.title = "x"

    print()
    print("-" * 30)
    print(window.document.title)

    print()
    print("-" * 30)
    window.document.title = "y"

    print()
    print("-" * 30)
    window.alert("z")
    window.document.title("hu")


#
