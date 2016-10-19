import asyncio
import websockets
import json
import cefevent


class Livechain(object):
    endpoint = 'wss://ws.blockchain.info/inv'

    def __init__(self, syslog=False, hostname=None, port=None):
        self.syslog = syslog
        self.hostname = hostname
        self.port = port

    def format_tx(self, tx, log_format='CEF'):
        if log_format == 'CEF':
            x = tx['x']
            out = x['out']
            inputs = x['inputs'][0]
            c = cefevent.CEFEvent()
            c.set_field('deviceEventClassId', tx['op'])
            c.set_field('externalId', x['tx_index'])
            c.set_field('deviceCustomString1', x['hash'])
            c.set_field('deviceCustomString1Label', 'Hash')
            c.set_field('bytesIn', inputs['prev_out']['value'])
            c.set_field('oldFileSize', x['size'])
            c.set_field('deviceVersion', str(x['ver']))
            c.set_field('endTime', x['time'])
            c.set_field('deviceAddress', x['relayed_by'])
            c.set_field('sourceUserName', inputs['prev_out']['addr'])
            c.set_field('sourceUserId', inputs['prev_out']['script'])

            c.set_field('deviceCustomNumber1', 1 if inputs['prev_out']['spent'] else 0)
            c.set_field('deviceCustomNumber1Label', 'Input Spent')

            for o in out:
                c.set_field('destinationUserName', o['addr'])
                c.set_field('destinationUserId', o['script'])
                c.set_field('bytesOut', o['value'])
                c.set_field('deviceCustomNumber2', 1 if o['spent'] else 0)
                c.set_field('deviceCustomNumber2Label', 'Output Spent')

                yield c




    async def listen(self, op='unconfirmed_sub'):
        async with websockets.connect(self.endpoint) as ws:
            await ws.send('{{"op":"{}"}}'.format(op))

            while True:
                result = await ws.recv()
                result = json.loads(result)

                logs = [l for l in self.format_tx(result)] 

                for l in logs:
                    print(l)
                    if self.syslog:
                        cs = cefevent.CEFSender([], self.hostname, self.port)
                        cs.send_log(l)

if __name__ == '__main__':
    lc = Livechain(syslog=True, hostname='127.0.0.1', port=10514)
    try:
        asyncio.get_event_loop().run_until_complete(lc.listen())
    except:
        pass
