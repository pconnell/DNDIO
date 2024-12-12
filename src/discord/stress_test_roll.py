from commands.dndio_parser import *
import dndio_pb2, dndio_pb2_grpc
import json
import grpc
import asyncio
from relay2 import grpc_relay

import multiprocessing,logging,sys,time
import pandas as pd

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler]
)
logger = logging.getLogger(__name__)

async def main(thr_val):

    relay = await grpc_relay('73.95.249.208','44443','./commands/dndio-tls.crt').connect()
    i = 0
    s = ''
    result_frame = pd.DataFrame({
        'status':[],
        'cmd_match':[],
        'total_time':[],
        'err_msg':[]
    })
    for i in range(5000):
        try:
            args = parser.parse_args(shlex.split("roll spell 'eldritch blast' 4"))
            args = vars(args)
            args['server'] = '1295825498231934987'
            args['user'] = 'chorky.'
            st = time.time()
            response = await relay.call(
                args
            )
            ed = time.time()
            d = {
                'status':response.status,
                'cmd_match':(
                    args['server']==response.dc_channel and
                    args['user']==response.dc_user and
                    args['cmd'] == response.cmd and
                    args['subcmd'] == response.subcmd
                ),
                'total_time':ed-st
            }
            result_frame.loc[len(result_frame)] = d
            if i % 100 == 0:
                logger.info(response.dierolls.total)
                
        except KeyboardInterrupt:
            logger.info('exiting...')
            result_frame.to_csv('./char_stress{}.txt'.format(s),index=False)
            break

        except:
            d = {
                'status':False,
                'cmd_match':False,
                'total_time':None
            }
            relay = await grpc_relay('73.95.249.208','44443','./commands/dndio-tls.crt').connect()
            pass
    out = open('./roll_stress{}.txt'.format(s),'w')
    out.write(s)
    out.close()

if __name__ == "__main__":
    #threads = []
    procs = []
    for i in range(5):
        proc = multiprocessing.Process(target=asyncio.run(main(i)))
        proc.start()
        proc.join()
    
    
    # for i in range(5):
    #     t = threading.Thread(target=asyncio.run(main()))
    #     threads.append(t)
    #     t.start()
    #     t.join()
