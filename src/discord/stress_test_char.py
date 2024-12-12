from commands.dndio_parser import *
import dndio_pb2, dndio_pb2_grpc
import json
import grpc
import asyncio
from relay2 import grpc_relay
import pandas as pd
import multiprocessing,logging,sys,time
from datetime import datetime
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
        'end_time':[]
    })
    for i in range(25000):
        if i %100 ==0:
            logger.info(i)
        try:
            args = parser.parse_args(shlex.split("char get all"))
            args = vars(args)
            args['server'] = '1295825498231934987'
            args['user'] = 'chorky.'
            st = time.time()
            response = await relay.call(
                args
            )
            ed = time.time()
            end_time = datetime.fromtimestamp(ed).isoformat()
            d = {
                'status':response.common.status,
                'cmd_match':(
                    args['server']==response.common.dc_channel and
                    args['user']==response.common.dc_user and
                    args['command'] + " " + args['subcommand'] + ' ' + args['info'][0] == response.common.orig_cmd
                ),
                'err_msg':response.common.err_msg,
                'total_time':ed-st,
                'end_time':end_time
            }
            # logger.info(d)
            result_frame.loc[len(result_frame)] = d       
            # if i % 100 == 0:
            #     # dat = json.loads(response.common.addtl_data)
            #     logger.info(response)
        except KeyboardInterrupt:
            logger.info('exiting...')
            result_frame.to_csv('./char_stress{}.txt'.format(s),index=False)
            break

        except Exception as e:
            d = {
                'status':False,
                'cmd_match':False,
                'total_time':None
            }
            print(e)
            result_frame.loc[len(result_frame)] = d
            relay = await grpc_relay('73.95.249.208','44443','./commands/dndio-tls.crt').connect()
            pass
    result_frame.to_csv('./char_stress{}.csv'.format(thr_val),index=False)

if __name__ == "__main__":
    procs = []
    asyncio.run(main(99))
    # for i in range(5):
    #     proc = multiprocessing.Process(target=asyncio.run(main(i)))
    #     proc.start()
    # for p in procs:
    #     proc.join()
    
