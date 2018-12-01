from . import autobind

import asyncio

from . import *
from .js_ws import *



loop = asyncio.get_event_loop()
coro = loop.create_server(JsServer, '127.0.0.1', 20080)
server = loop.run_until_complete(coro)
print('serving on {}'.format(server.sockets[0].getsockname()))


window = CallPath(None,'window')

async def __main__():
    while aio.lives:
        await asyncio.sleep(1)


from aioprompt import *
run(__main__)


