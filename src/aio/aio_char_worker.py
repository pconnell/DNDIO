##################################################################
import aio_pika,os,json,uuid,logging,sys
from concurrent import futures
import uuid
from typing import MutableMapping
from aio_pika.abc import (
    AbstractChannel, AbstractConnection, AbstractIncomingMessage, AbstractQueue,
)
from aio_pika import Message
import asyncio
# import workerChar_pb2, workerChar_pb2_grpc
import dndio_pb2, dndio_pb2_grpc
import json


RMQ_HOST = os.getenv('RMQ_HOST') or 'localhost'
RMQ_PORT = os.getenv('RMQ_PORT') or 5672

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler]
)
logger = logging.getLogger(__name__)
##################################################################

ERR_MSGS = {
    'no_char':"A character for this user does not exist in the database.  Please use the init command for this user first.",
    'no_spellcast':"Your character class is not a spellcasting class, so you do not have spellslots, spellcasting ability, spell attack rolls, or spell DC values.",
    'invalid_cmd':"The provided command is invalid",
    'not_implemented':"The code for this feature is not yet implemented",
    'db_err':"There was an unknown database error for this command.",
    'implementation_err':"There's a bug in the code for this command."
}

##################################################################
class rmq_client():
    connection: AbstractConnection
    channel: AbstractChannel
    callback_queue: AbstractQueue
    def __init__(self,url):
        self.url = url
        self.futures: MutableMapping[str,asyncio.Future] = {}
    async def connect(self):
        logger.info("  [x] Establshing client connection to rmq db channel")
        self.connection = await aio_pika.connect(self.url)
        self.channel = await self.connection.channel()
        logger.info("  [x] establishing callback queue")
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        await self.callback_queue.consume(self.on_response,no_ack=True)
        logger.info("  [x] client connection with callback queue established!")
        return self
    async def on_response(self, msg: AbstractIncomingMessage):
        if msg.correlation_id is None:
            logger.info(" [!] Received bad inbound response: {}".format(msg))
            return
        logger.info("  [!!!] futures: {}".format(self.futures))
        future: asyncio.Future = self.futures.pop(msg.correlation_id)
        logger.info("  [!!!] futures: {}".format(self.futures))
        future.set_result(msg.body)
        
    async def call(self,msg,correlation_id):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.futures[correlation_id] = future
        logger.info("  [!!!] futures: {}".format(self.futures))
        await self.channel.default_exchange.publish(
            Message(
                msg.encode('utf-8'),
                content_type='text/plain',
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name
            ),
            routing_key='worker.db'
        )
        return await future
##################################################################

##################################################################
class rmq_server():
    def __init__(self,url,qname):
        self.connection = None
        self.channel = None 
        self.exchange = None
        self.queue = None
        self.qname = qname
        self.url = url
        self.rmq_client = rmq_client(url)

    async def connect(self):
        logger.info(" [x] Initializing RabbitMQ Async Connection")
        self.connection = await aio_pika.connect(
            self.url
        )
        logger.info(" [x] Connecting to RabbitMQ channel")
        self.channel = await self.connection.channel()
        self.exchange=self.channel.default_exchange
        logger.info(" [x] Establishing request queue: {}".format(self.qname))
        self.queue = await self.channel.declare_queue(self.qname)
        logger.info(" [x] Char Worker Listening for RPC Requests")

    #when can certain things not be set? and where should that be handled?

        # character stats between 1 and 20?

        # proficiency bonus - automatically handle?

        # a spell that's outside of the character's class

    async def add_char(self,msg):
        #adding items, spells, and feats
        args = json.loads(msg.args)
        funcs = {
            'name':self.add_feat,
            'item':self.add_item,
            'spell':self.add_spell
        }
        f = [a for a in list(args.keys()) if a not in ['command','subcommand']][0]
        if not funcs.get(f):
            err_msg = await self.proc_err_msg(
                msg,
                'char add',
                ERR_MSGS['invalid_cmd']
            )
            return err_msg
        else:
            func = funcs[f] #list(args.keys())[0]]
            return await func(msg)

    async def add_feat(self,msg):
        #need to make sure of the following:
            # character exists
            # feat is not already in list of feats
            # feat exists and pertains to the character class
        not_implemented = True
        if not_implemented: 
            err_msg = await self.proc_err_msg(
                msg,
                'char add feat',
                ERR_MSGS['not_implemented']
            )
            return err_msg
        else:
            args = json.loads(msg.args)
            err_msg = ''
            char_query = """SELECT char_classes,feats FROM char_table WHERE char_id='{}' and campaign_id='{}';""".format(
                msg.dc_channel, msg.user
            )
            corr_id = str(uuid.uuid4())
            char_resp = await self.rmq_client.call(char_query,corr_id)
            if len(char_resp['rows']) == 0:
                err_msg = await self.proc_err_msg(
                    #char does not exist in this campaign
                    msg,
                    "char add feat",
                    ERR_MSGS['no_char']
                )
                return err_msg
            char_resp = char_resp['rows'][0]
            to_add = []
            for f in args.values():
                if not f in char_resp['feats']:
                    to_add.apppend(f)
                else:
                    err_msg += "You already have {} in your character feats".format(f)
            
            resps = []
            qstr = "','".join(to_add)
            qstr = "('"+"')"
            feat_query = """SELECT * FROM feats WHERE name IN {}""".format(qstr)
            corr_id = str(uuid.uuid4())
            feat_resp = await self.rmq_client.call(feat_query,corr_id)
            feat_resp = feat_resp['rows']
            existing_feats = [f['name'] for f in feat_resp if f['char_class']==char_resp['char_classes']]
            for f in to_add:
                if f not in existing_feats:
                    err_msg+='Error: feat {} does not exist for your character class'

    async def check_char_exists(self,msg):
        char_query = """SELECT * FROM char_table WHERE char_id='{}' and campaign_id='{}';""".format(
            msg.user, msg.dc_channel
        )
        corr_id = str(uuid.uuid4())
        char_resp = await self.rmq_client.call(char_query,corr_id)
        char_resp = json.loads(char_resp)
        logger.info(char_resp)
        if len(char_resp['rows']) > 0:
            return (True,char_resp['rows'][0])
        else:
            return (False,None)
            

    async def check_feat_exists(self,msg):
        return False

    async def check_item_exists(self,msg):
        try:
            q1 = """SELECT name FROM weapons"""
            args = json.loads(msg.args)
            corr_id = str(uuid.uuid4())
            wep_resp = await self.rmq_client.call(q1,corr_id)
            wep_data = json.loads(wep_resp)['rows']
            q2 = """SELECT name FROM armor"""
            corr_id = str(uuid.uuid4())
            arm_resp = await self.rmq_client.call(q2,corr_id)
            arm_data = json.loads(arm_resp)['rows']
            weps = [w['name'] for w in wep_data]
            arm = [a['name'] for a in arm_data]
            # res = {True:[],False:[]}
            res = {'armor':[],'weapons':[],'non_existent':[]}
            for item in args['item']:
                if item in weps:
                    res['weapons'].append(item)
                elif item in arm:
                    res['armor'].append(item)
                else:
                    res['non_existent'].append(item)
            return res
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                'check item exists',
                ERR_MSGS['implementation_err']+'\n{}'.format(str(e))
            )
            return err_msg

    async def check_spell_exists(self,msg,char_class,char_level):
        try:
            spell_level = (char_level - 1)//2
            q1 = """SELECT name FROM spells WHERE char_classes CONTAINS '{}' AND level <= {} allow filtering;""".format(char_class,spell_level)
            corr_id = str(uuid.uuid4())
            spell_resp = await self.rmq_client.call(q1,corr_id)
            spellnames = json.loads(spell_resp)
            spellnames = [s['name'] for s in spellnames['rows']]
            args = json.loads(msg.args)
            res = {True:[],False:[]}
            for spell in args['spell']:
                if spell not in spellnames:
                    res[False].append(spell)
                else:
                    res[True].append(spell)
            return res
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                'check spell exists',
                ERR_MSGS['implementation_err'] +'\n{}'.format(str(e))
            )
            return err_msg

    async def check_skill_exists(self, skills:list):
        try:
            query = """SELECT * FROM skills;"""
            corr_id=str(uuid.uuid4())
            resp = await self.rmq_client.call(query,corr_id)
            resp = json.loads(resp)
            skillnames = set([s['name'] for s in resp])
            skills = set(skills)
            #do the intersection and the difference?
            to_add = list(skills.intersection(skillnames))
            cant_add = list(skills.difference(skillnames))
            return {
                True:to_add,
                False:cant_add
            }
        except Exception as e:
            err_msg = await self.proc_err_msg(
                skills,
                'check skill exists',
                ERR_MSGS['implementation_err']+'\n{}'.format(str(e))
            )
            return err_msg

    async def add_item(self,msg):
        #need to make sure of the following:
            # character exists
            # item is not already in list of items
            # item exists (armor or weapon only)
        try:
            status = False
            args = json.loads(msg.args)
            err_msg = ''
            char_data = await self.check_char_exists(msg)
            if not char_data[0]:
                err_msg = await self.proc_err_msg(
                    msg,
                    'char add item',
                    ERR_MSGS['no_char']
                )
                return err_msg
            char_data = char_data[1]
            items = await self.check_item_exists(msg)
            no_add = items.pop('non_existent')
            present = []
            addable = {}
            for v in ['armor','weapons']:
                if char_data.get(v,False):
                    tmp = list(set(char_data[v]).union(items[v]))
                    present.extend(list(set(char_data[v]).difference(items[v])))
                    addable[v] = list(tmp)
                    char_data[v] = tmp #list(set(char_data[v]).union(items[v]))
                else:
                    addable[v] = items[v]
                    char_data[v] = items[v]
            if len(items['armor']) > 0 or len(items['weapons']) > 0:
                add_query = """UPDATE char_table SET weapons={}, armor={} WHERE char_id='{}' and campaign_id='{}' IF EXISTS;""".format(
                    char_data['weapons'],char_data['armor'],char_data['char_id'],char_data['campaign_id']
                )
                # add_query = """UPDATE char_table SET inventory={} WHERE char_id='{}' and campaign_id='{}' IF EXISTS;""".format(
                #     char_data['inventory'],msg.user,msg.dc_channel
                # )
                corr_id = str(uuid.uuid4())
                resp = await self.rmq_client.call(add_query,corr_id)
                if len(no_add) > 0:
                    err_msg+="The following items are not available in the system weapons or armor tables: {}".format(no_add)
                adds = []
                for k,v in addable.items():
                    adds.append(len(v) > 0)
                if True not in adds:
                    err_msg+="All the items provided are already in your inventory."
                status=True
            else:
                #no items to add
                err_msg+="None of the items you entered are avaialbe in the system: {}".format(args['item'])
                status=False
            
            c = dndio_pb2.dndioreply(
                status=status,
                dc_channel=msg.dc_channel,
                dc_user=msg.user,
                addtl_data='',
                err_msg=err_msg
            )
            char_reply = dndio_pb2.charreply(
                common = c
            )
            return char_reply
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                'add_item()',
                ERR_MSGS['implementation_err']+'\n{}'.format(str(e))
            )
            return err_msg
    
    async def add_spell(self,msg):
        try:
            char_data = await self.check_char_exists(msg)
            if not char_data[0]:
                err_msg = await self.proc_err_msg(
                    msg,
                    'char add spell',
                    ERR_MSGS['no_char']
                )
                return err_msg
            char_data=char_data[1]
            spellnames = await self.check_spell_exists(
                msg,char_data['char_class'],char_data['level']
            )
            if len(spellnames[True]) == 0:
                return await self.proc_err_msg(
                    msg,
                    'char add spell',
                    "No spells to add - spells aren't present in the database"
                )
            can_add = set(spellnames[True])
            if char_data['spells'] is None:
                char_data['spells'] = []
            can_add = list(can_add.difference(char_data['spells']))
            # logger.info("[***************************************************************************] can add: {}".format(can_add))
            if len(can_add) > 0:
                add_query = """UPDATE char_table SET spells = spells+{} WHERE char_id='{}' and campaign_id='{}' IF EXISTS;""".format(
                    can_add,
                    char_data['char_id'],
                    char_data['campaign_id']
                )
                logger.info(add_query)
                corr_id = str(uuid.uuid4())
                resp = await self.rmq_client.call(add_query,corr_id)
                resp = json.loads(resp)
                if resp['success']:
                    c=dndio_pb2.dndioreply(
                        status=True,
                        dc_channel=msg.dc_channel,
                        dc_user=msg.user
                    )
                else:
                    c = dndio_pb2.dndioreply(
                        status=False,
                        dc_channel=msg.dc_channel,
                        dc_user=msg.dc_user,
                        err_msg=ERR_MSGS['db_err']
                    )
                ret = dndio_pb2.charreply(
                    common=c
                )
                return ret
            else:
                err_msg =  await self.proc_err_msg(
                    msg,
                    'char add spell',
                    "No spells to add - all listed spells are already known by your character."
                )
                return err_msg
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                'add_spell',
                ERR_MSGS['implementation_err'] +'\n{}'.format(str(e))
            )
            return err_msg

    async def char_set(self,msg):
        try:
            args = json.loads(msg.args)
            char_data = await self.check_char_exists(msg)

            if not char_data[0]:
                err_msg = await self.proc_err_msg(
                    msg,
                    'char set',
                    ERR_MSGS['no_char']
                )
                return err_msg
            char_data = char_data[1]
            # """ valid mutex fields:
            # ability - list of dictionaries
            # skill - list (maybe still with k/v pairs?)
            # AC - single value
            # class
            # race
            # size
            # level
            # name
            # """
            logger.info("[!!!!!] {}".format(args))
            to_set = [a for a in list(args.keys()) if a not in ['command','subcommand','user','server']][0]
            logger.info("[!!!!!] {}".format(to_set))
            query = ""
            if to_set == 'ability':
                qstr = ''
                for k,v in args['ability'].items():
                    qstr+='{}={},'.format(k,v)
                qstr = qstr[:-1]
                query = "UPDATE char_table SET {} WHERE char_id='{}' AND campaign_id='{}' IF EXISTS;".format(
                    qstr,char_data['char_id'],char_data['campaign_id']
                )
            elif to_set == 'proficiency':
                # skill_data = await self.check_skill_exists(args[to_set])
                # logger.info("[!!!!!] {}".format(to_add))
                if char_data['skills'] is None:
                    char_data['skills'] = []
                char_skills = set(char_data['skills'])
                to_add = list(
                    set(args[to_set]).difference(char_skills)
                )
                query = "UPDATE char_table SET skills = skills + {} WHERE char_id='{}' AND campaign_id='{}' IF EXISTS;".format(
                    to_add,char_data['char_id'],char_data['campaign_id']
                )
                
            elif to_set == 'AC':
                query = "UPDATE char_table SET ac={} WHERE char_id='{}' AND campaign_id='{}' IF EXISTS".format(
                    args['AC'],char_data['char_id'],char_data['campaign_id']
                )
            elif to_set=='race':
                query = "UPDATE char_table SET race='{}' WHERE char_id='{}' AND campaign_id='{}' IF EXISTS".format(
                    args['race'],char_data['char_id'],char_data['campaign_id']
                )
            elif to_set=='size':
                query = "UPDATE char_table SET size='{}' WHERE char_id='{}' AND campaign_id='{}' IF EXISTS".format(
                    args['size'],char_data['char_id'],char_data['campaign_id']
                )
            elif to_set=='level':
                # need to handle if both level and class are set to pull over any needed data? 
                query = "UPDATE char_table SET level={} WHERE char_id='{}' AND campaign_id='{}' IF EXISTS".format(
                    args['level'],char_data['char_id'],char_data['campaign_id']
                )
            elif to_set =='name':
                query = "UPDATE char_table SET char_name='{}' WHERE char_id='{}' AND campaign_id='{}' IF EXISTS".format(
                    args['name'],char_data['char_id'],char_data['campaign_id']
                )
            elif to_set =='class':
                query = "UPDATE char_table SET char_class='{}' WHERE char_id='{}' AND campaign_id='{}' IF EXISTS".format(
                    args['class'],char_data['char_id'],char_data['campaign_id']
                )
            if (
                to_set == 'level' and char_data['char_class'] is not None or
                to_set == 'class' and char_data['level'] is not None
            ):
                #handling code here for updating spellslots or other stuff...
                pass
            if query != '':
                corr_id=str(uuid.uuid4())
                resp = await self.rmq_client.call(query,corr_id)
                resp = json.loads(resp)
            else: 
                err_msg = await self.proc_err_msg(
                    msg,
                    'char set '+to_set,
                    err_msg='The issued query to the database was blank.'
                )
                return err_msg
            logger.info("{}: {}".format(type(msg),msg))
            if resp['success']:
                logger.info("{}: {}".format(type(msg),msg))
                #we're good
                c = dndio_pb2.dndioreply(
                    orig_cmd='char set '+to_set,
                    dc_channel=msg.dc_channel,
                    dc_user=msg.user,
                    addtl_data='',
                    err_msg=''
                )
                char_reply = dndio_pb2.charreply(
                    common=c
                )
                return char_reply 
            else:
                #query didn't work
                err_msg = await self.proc_err_msg(
                    msg,
                    'char set '+to_set,
                    err_msg=ERR_MSGS['db_err']
                )
                return err_msg
        except Exception as e:
            import traceback
            err_msg = await self.proc_err_msg(
                msg,
                'char set',
                ERR_MSGS['implementation_err']+'\n{}: {}'.format(e,traceback.format_exc(e))
            )
            return err_msg

    async def set_char(self,msg):
        try:
            campaign = msg.dc_channel,
            user = msg.user
            args = json.loads(msg.args)
            funcs = {
                'ability':self.ability_char,
                'skill':self.skill_char,
                'item':self.add_char,
                'spell':self.spell_char,
            }
            func = funcs[list(args.keys())[0]] #['action']]
            resp = await func(args)
            return resp 
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                'set char',
                ERR_MSGS['implementation_err']+'\n{}'.format(str(e))
            )
            return err_msg
        
    async def get_char(self,msg):
        try:
            args = json.loads(msg.args)
            logger.info(args)
            to_get = args['info']
            char_resp = await self.check_char_exists(msg)
            # char_resp = json.loads(char_resp)
            if not char_resp[0]:
                err_msg = await self.proc_err_msg(
                    msg,
                    'char get',
                    ERR_MSGS['no_char']
                )
                return err_msg
            char_data = char_resp[1]
            ret_data = {}
            if 'all' in to_get:
                ret_data.update(char_data)
            if 'ability' in to_get:
                for item in ['cha','str','wis','int','con','dex']:
                    ret_data[item.upper()] = char_data[item.lower()]
            if 'skills' in to_get:
                ret_data.update({'skills':char_data['skills']})
            if 'combat' in to_get:
                for item in ['max_hp','curr_hp','ac','dex','equipped']:
                    ret_data[item] = char_data[item]
            if 'inv' in to_get:
                ret_data.update({'armor':char_data['armor'], 'weapons':char_data['weapons']})
            if 'spellmod' in to_get:
                query = "SELECT spell_atk_mod, spell_dc FROM class_start WHERE char_class = '{}'".format(
                    char_data['char_class']
                )
                corr_id = str(uuid.uuid4())
                class_resp = await self.rmq_client.call(query,corr_id)
                class_resp = json.loads(class_resp)['rows'][0]
                query = "SELECT prof_bonus,spellslots FROM classes WHERE class_id='{}-{}'".format(
                    char_data['char_class'],char_data['level']
                )
                corr_id = str(uuid.uuid4())
                class_lvl_resp = await self.rmq_client.call(query,corr_id)
                class_lvl_resp = json.loads(class_lvl_resp)['rows'][0]
                if not isinstance(class_resp['spell_atk_mod'],str):
                    err_msg = await self.proc_err_msg(
                        msg,
                        'char get '+to_get,
                        ERR_MSGS['no_spellcast']
                    )
                    return err_msg
                full_spell_mod = class_resp['spell_atk_mod']
                # logger.info("[!!!!!!] {}".format(full_spell_mod))
                spell_mod = class_resp['spell_atk_mod'].split('+')[1].lower()
                spell_mod_value = (char_data[spell_mod]-10)//2
                spell_mod_value+=class_lvl_resp['prof_bonus']
                spell_dc = 8 + class_lvl_resp['prof_bonus'] + (char_data[spell_mod]-10)//2
#                 c = dndio_pb2.dndioreply(
#                     status=True,
#                     orig_cmd='char get spellmod',
#                     dc_channel=msg.dc_channel,
#                     dc_user=msg.user,
#                     addtl_data='''As a level {} {}, your spell modifier is {}({}).
# Your full spell modifier is calculated by {} which is {}.'''.format(
#                         char_data['level'],
#                         char_data['char_class'],
#                         spell_mod.upper(),
#                         (char_data[spell_mod]-10)//2,
#                         full_spell_mod,
#                         spell_mod_value
#                     ),
#                     err_msg = ""
#                 )
#                 m = dndio_pb2.charreply(
#                     common=c
#                 )
                # return m
                ret_data.update({
                    'spellcast_modifier':full_spell_mod,
                    'spellcast_mod_value':spell_mod_value,
                    'spell_dc':class_resp['spell_dc'],
                    'spell_dc_value':spell_dc,
                })
            if 'AC' in to_get:
                ret_data.update({'AC':char_data['ac']})
            if 'level' in to_get:
                ret_data.update({'level':char_data['level']})
            if 'class' in to_get:
                ret_data.update({'class':char_data['char_class']})
            if 'equipped' in to_get:
                ret_data.update({'equipped':char_data['equipped']})
            if 'spells' in to_get:
                ret_data.update({'spells':char_data['spells']})
            # logger.info("[!!!!!!] {}".format(ret_data))
            c = dndio_pb2.dndioreply(
                orig_cmd = 'char get {}'.format(to_get),
                dc_channel=msg.dc_channel,
                dc_user=msg.user,
                addtl_data=json.dumps(ret_data),
                err_msg=''
            )
            r = dndio_pb2.charreply(
                common=c
                #need more here...
            )
            return r
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                'get char',
                ERR_MSGS['implementation_err']+'\n{}'.format(str(e))
            )
            return err_msg

    async def remove_char(self,msg):
        not_implemented= True 
        if not_implemented:
            err_msg = await self.proc_err_msg(
                msg,
                'char remove',
                ERR_MSGS['not_implemented']
            )
            return err_msg

    async def proc_err_msg(self,msg,cmd,err_msg):
        c = dndio_pb2.dndioreply(
            orig_cmd=cmd,
            dc_channel=msg.dc_channel,
            dc_user=msg.user,
            err_msg=err_msg
        )
        char_reply = dndio_pb2.charreply(
            common=c
        )
        return char_reply 

    async def run(self):
        await self.connect()
        self.rmq_client = await self.rmq_client.connect()
        async with self.queue.iterator() as qiter:
            msg: AbstractIncomingMessage
            async for msg in qiter:
                try:
                    assert msg.reply_to is not None
                    # do processing here...
                    logger.info("  [x] Received new RPC request: {}".format(msg))
                    
                    inbound_msg = dndio_pb2.dndiomsg()
                    inbound_msg.ParseFromString(msg.body)
                    logger.info("  [x] Parsed RPC to GRPC, converting to query")
                    ##### HERE'S WHERE WE'LL PARSE THE MESSAGE FROM THE CLIENT
                    ## AND USE THAT TO CRAFT DIFFERENT QUERIES
                    ## the parsed command gets fed to one of the above char get/set functions
                    ## and it will handle the query routing and response
                    ## each will return a response to this function, and this function
                    ## will send the final message.
                    funcs = {
                        'set':self.char_set,
                        'get':self.get_char,
                        'add':self.add_char,
                        'remove':self.remove_char
                    }
                    func = funcs.get(inbound_msg.subcmd,None)
                    if func is None:
                        resp = await self.proc_err_msg(
                            inbound_msg,
                            "{} {}".format(inbound_msg.cmd, inbound_msg.subcmd),
                            ERR_MSGS['invalid_cmd']
                        )
                    else:
                        resp = await func(inbound_msg)
                        logger.info("  [x] Response to query received: {}".format(resp))
                        logger.info("  [x] Publishing response".format(resp))
                        await self.exchange.publish(
                            Message(
                                body=resp.SerializeToString(),
                                correlation_id=msg.correlation_id
                            ),
                            routing_key=msg.reply_to
                        )
                    logging.info(' [x] Processed Request')
                except Exception:
                    logging.exception(" [!] Error processing for message: {}".format(msg))



if __name__=='__main__':
    worker = rmq_server("amqp://guest:guest@{}:{}".format(RMQ_HOST,RMQ_PORT),'grpc.workerchar')
    asyncio.run(worker.run())