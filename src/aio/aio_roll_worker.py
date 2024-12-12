##################################################################
import aio_pika,os,json,uuid,logging,sys
from concurrent import futures
import uuid
from typing import MutableMapping
from aio_pika.abc import (
    AbstractChannel, AbstractConnection, AbstractIncomingMessage, AbstractQueue,
)
from aio_pika import Message
# from pika import BasicProperties
import asyncio
# import workerRoll_pb2, workerRoll_pb2_grpc
import dndio_pb2, dndio_pb2_grpc
# from src.discord.commands import dndio_pb2, dndio_pb2_grpc
import random 
from argparse import Namespace
##################################################################

##################################################################
RMQ_HOST = os.getenv('RMQ_HOST') or 'localhost'
RMQ_PORT = os.getenv('RMQ_PORT') or 5672

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.DEBUG,#INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[handler]
)
logger = logging.getLogger(__name__)
##################################################################
ERR_MSGS = {
    'no_char':"A character for this user does not exist in the database.  Please use the init command for this user first.",
    'no_spellcast':"Your character class is not a spellcasting class, so you do not have spellslots, spellcasting ability, spell attack rolls, or spell DC values.",
    'invald_cmd':"The provided command is invalid",
    'not_implemented':"The code for this feature is not yet implemented",
    'db_err':"There was an unknown database error for this command.",
    'imp_err':"There's a bug in the code for this function.",
    'char_err':"Unable to perform function: your character is not fully initialized.  Use char set/add/get commands to fully initialize your character."
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
        await self.callback_queue.consume(self.on_response,no_ack=False) #True)
        logger.info("  [x] client connection with callback queue established!")
        return self
    async def on_response(self, msg: AbstractIncomingMessage):
        if msg.correlation_id is None:
            logger.info(" [!] Received bad inbound response: {}".format(msg))
            return
        logger.debug("  [!!!] futures: {}".format(self.futures))
        future: asyncio.Future = self.futures.pop(msg.correlation_id)
        logger.debug("  [!!!] futures: {}".format(self.futures))
        future.set_result(msg.body)
        
    async def call(self,msg,correlation_id):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.futures[correlation_id] = future
        logger.debug("  [!!!] futures: {}".format(self.futures))
        await self.channel.default_exchange.publish(
            Message(
                msg.encode('utf-8'),
                content_type='text/plain',
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
                expiration=10
            ),
            routing_key='worker.db'
        )
        return await future
##################################################################


QUERIES = {
    'get_char': "SELECT * FROM char_table WHERE char_id='{}' and campaign_id='{}' allow filtering;",
    'get_wep': "SELECT * FROM weapons WHERE id={};",
    #'get_armor': "SELECT * FROM armor WHERE id={}",
    'get_spells': "SELECT * FROM spells WHERE id IN ({}) allow filtering;",
    'get_class':"SELECT * FROM classes WHERE class_id = '{}-{}';"
}

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

    async def check_char_exists(self,msg):
        char_query = """SELECT * FROM char_table WHERE char_id='{}' and campaign_id='{}';""".format(
            msg.user, msg.dc_channel
        )
        corr_id = str(uuid.uuid4())
        char_resp = await self.rmq_client.call(char_query,corr_id)
        char_resp = json.loads(char_resp)
        logger.debug(char_resp)
        if len(char_resp['rows']) > 0:
            return (True,char_resp['rows'][0])
        else:
            return (False,None)
        
    async def roll_raw(self,msg):
        try:
            args = json.loads(msg.args)
            rolls = []
            # if args.get('advantage') or args.get('disadvantage'):
            add = max([args.get('advantage'),args.get('disadvantage'),0])
            ks = list(args['rolls'].keys())
            vs = list(args['rolls'].values())
            mds = args['modifiers']
            for i in range(len(ks)):
                k,v,m = int(ks[i]),int(vs[i]),int(mds[i])
                logger.debug("{}:{}:{}".format(k,v,m))
                drolls = [random.randint(1,k) for i in range(v+add)]
                modified = [r+m for r in drolls]
                if args.get('disadvantage') > 0:
                    tot = min(modified)
                elif args.get('advantage') > 0:
                    tot = max(modified)
                else:
                    tot = sum(modified)
                rolls.append(
                    dndio_pb2.roll(
                        roll_type='raw',
                        die_rolls=drolls,
                        modifiers=[m],
                        modified_rolls=modified,
                        total=tot
                    )
                )
                # for k,v in args['rolls'].items():
                #     r = [random.randint(1,int(k)) for i in range(int(v)+int(add))]
                #     if args.get('disadvantage'):
                #         tot = min(r)
                #     else:
                #         tot = max(r)
                #     rolls.append(
                #         dndio_pb2.roll(
                #             roll_type='raw',
                #             die_rolls=r,
                #             modifiers=None,
                #             modified_rolls=None,
                #             total = tot
                #         )
                #     )
            # else:
            #     rolls = []
            #     for k,v in args['rolls'].items():
            #         r = [random.randint(1,int(k)) for i in range(int(v))]
            #         if args.get('disadvantage'):
            #             tot = min(r)
            #         else:
            #             tot = max(r)
            #         rolls.append(
            #             dndio_pb2.roll(
            #                 roll_type='raw',
            #                 die_rolls=r,
            #                 modifiers=None,
            #                 modified_rolls=None,
            #                 total = tot
            #             )
            #         )
            common = dndio_pb2.dndioreply(
                orig_cmd=msg.cmd,
                status = True,
                dc_channel=msg.dc_channel,
                dc_user=msg.user,
                addtl_data=None,
                err_msg=None
            )
            roll_reply = dndio_pb2.rollreply(
                common=common,
                dierolls=rolls
            )
            logger.debug("  [x] roll reply: {}".format(roll_reply))
            # await asyncio.sleep(.1)
            return roll_reply
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                "roll raw",
                ERR_MSGS['imp_err'] + " " + str(e)
            )
            return err_msg

    async def roll_initiative(self,msg):
        ### still need to handle advantage/disadvantage, subcmd vs cmd vs args...

        try:
            # loop = asyncio.get_running_loop()
            # task = loop.create_task(self.check_char_exists(msg))
            # char_dat = await task
            char_dat = await self.check_char_exists(msg)
            if not char_dat[0]:
                err_msg = await self.proc_err_msg(
                    msg,
                    'roll initiative',
                    ERR_MSGS['no_char']
                )
                return err_msg
            char_resp = char_dat[1]
            args = json.loads(msg.args)
            dex_mod = char_resp.get('dex',None)
            if not dex_mod:
                err_msg = await self.proc_err_msg(
                    msg,
                    'roll initiative',
                    ERR_MSGS['char_err']
                )
                return err_msg
            mod = (dex_mod-10)//2
            ##determine if we need more dice to roll for advantage / disadvantage
            if args['advantage']:
                add = int(args['advantage'])
            elif args['disadvantage']:
                add = int(args['disadvantage'])
            else:
                add = 0
            #roll the dice
            rolls = [random.randint(1,20) for i in range(1+add)]
            # add the modifier
            mod_rolls = [r+mod for r in rolls]
            #select the roll based on advantage/disadvantage
            if args['advantage']:
                total = max(mod_rolls)
            elif args['disadvantage']:
                total = min(mod_rolls)
            else:
                total = max(mod_rolls)
            #build the roll object
            r = dndio_pb2.roll(
                roll_type='initiative',
                die_rolls=rolls,
                modifiers=[mod],
                modified_rolls=mod_rolls,
                total = total
            )
            #build the common reply object
            c = dndio_pb2.dndioreply(
                orig_cmd='roll initiative',
                status=True,
                dc_channel=msg.dc_channel,
                dc_user=msg.user,
                addtl_data='',
                err_msg=''
            )
            #build the roll reply using the other reply objects
            resp = dndio_pb2.rollreply(
                common=c,
                dierolls=[r]
            )
            #return the response
            return resp
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                "roll initiative",
                ERR_MSGS['imp_err'] + " " + str(e)
            )
            return err_msg
    
    async def roll_check(self,msg):
        try:
            logger.debug(msg)
            char_resp = await self.check_char_exists(
                msg
            )
            if not char_resp[0]:
                err_msg = await self.proc_err_msg(
                    msg,
                    "roll check",
                    ERR_MSGS['char_err']
                )
                return err_msg
            args = json.loads(msg.args)
            char_resp=char_resp[1]
            logger.debug(args['ability'])
            if args['ability'] not in ['CHA','WIS','CON','INT','DEX','STR']:
                resp = await self.roll_skill(msg)
                return resp 
            stat = char_resp[args['ability'].lower()]
            adv = int(args.get('advantage') or 0)
            dadv = int(args.get('disadvantage') or 0)
            dice = 1 + adv+dadv
            mod = (stat-10)//2
            rolls = [random.randint(1,20) for i in range(dice)]
            mod_rolls = [r+mod for r in rolls]

            c = dndio_pb2.dndioreply(
                orig_cmd='',
                status=True,
                dc_channel=msg.dc_channel,
                dc_user=msg.user,
                addtl_data='Your {} modifier is {}.'.format(args['ability'],mod),
                err_msg=''
            )

            r = dndio_pb2.roll(
                roll_type='{} check'.format(args['ability']),
                die_rolls=rolls,
                modifiers=[mod],
                modified_rolls=mod_rolls,
                total = 0
            )

            reply = dndio_pb2.rollreply(
                common=c,dierolls=[r]
            )
            return reply
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                "roll check",
                ERR_MSGS['imp_err'] + " " + str(e)
            )
            return err_msg
        pass

    # async def roll_save(self,msg):
    #     try:
    #         char_resp = await self.check_char_exists(
    #             msg
    #         )
    #         if not char_resp[0]:
    #             err_msg = await self.proc_err_msg(
    #                 msg,
    #                 "roll check",
    #                 ERR_MSGS['char_err']
    #             )
    #             return err_msg
    #         args = json.loads(msg.args)

    #     except Exception as e:
    #         err_msg = await self.proc_err_msg(
    #             msg,
    #             "roll initiative",
    #             ERR_MSGS['imp_err'] + " " + str(e)
    #         )
    #         return err_msg
    #     pass

    async def roll_save(self,msg):#,campaign, char, stat):
        try:
            args = json.loads(msg.args)
            stat = args['ability'].lower() #','.join(args['ability']).lower()
            campaign = msg.dc_channel
            char=msg.user
            adv = int(args.get('advantage') or 0)
            dadv = int(args.get('disadvantage') or 0)
            # adv = int(args.get('advantage',0))
            # dadv = int(args.get('disadvantage',0))
            cmd = 'roll-save'
            char_query = """SELECT char_class,level,{} from char_table where campaign_id='{}' and char_id='{}' allow filtering;""".format(
                stat,campaign,char
            )
            corr_id = str(uuid.uuid4())
            char_resp = await self.rmq_client.call(char_query,corr_id)
            char_resp = json.loads(char_resp)['rows'][0]
            logger.debug("[!!!!!!!!!!!!!] {}".format(char_resp))
            if not char_resp.get(stat,False):
                err_msg = await self.proc_err_msg(
                    msg,
                    cmd,
                    'Your character is not fully initialized and has no value set for {}'.format(stat.upper())
                )
                return err_msg
            ability_mod = (char_resp[stat]-10)//2 #do some math to get the modifier
            class_st_query = """SELECT proficiencies['Saving Throws'] FROM class_start WHERE char_class='{}'""".format(char_resp['char_class'],char_resp['level'])
            class_query = """SELECT prof_bonus FROM classes WHERE class_id='{}';""".format(
                char_resp['char_class'] + '-' + str(char_resp['level'])
            )
            corr_id = str(uuid.uuid4())
            class_st_resp = await self.rmq_client.call(class_st_query,corr_id)
            class_st_resp = json.loads(class_st_resp)['rows'][0]
            proficiencies = class_st_resp['proficiencies__Saving_Throws']
            # logger.info(" [!!!] {}".format(proficiencies,))
            corr_id = str(uuid.uuid4())
            class_resp = await self.rmq_client.call(class_query,corr_id)
            logger.debug("[!!!!!!!!!!!!!] {}".format(json.loads(class_resp)))
            class_resp = json.loads(class_resp)['rows'][0]
            logger.debug(" [!!!] {}\t{}".format(proficiencies,class_resp))
            # mod = class_resp['prof_bonus']
            addtl_data = ""
            modifiers = []
            modifiers.append(ability_mod)
            add = adv+dadv
            roll = [random.randint(1,20) for i in range(1+add)]
            mod_roll = []
            if stat.upper() in proficiencies:
                addtl_data+= "You're proficient in {} saves - so you add your proficiency bonus ({})\n".format(
                    stat.upper(),
                    class_resp['prof_bonus']
                )
                modifiers.append((class_resp['prof_bonus']))
                mod_roll= [r+class_resp['prof_bonus']+ability_mod for r in roll]
            else:
                mod_roll+=[r+ability_mod for r in roll]
            if adv > 0:
                total = max(mod_roll)
            elif dadv > 0:
                total = min(mod_roll)
            else:
                total = max(mod_roll)
            r = dndio_pb2.roll(
                roll_type='{} save'.format(stat.upper()),
                die_rolls=roll,
                modifiers=modifiers,
                modified_rolls=mod_roll,
                total = total
            )
            #build the common reply object
            addtl_data+='Your {} modifier is {}'.format(
                stat.upper(),ability_mod
            )
            c = dndio_pb2.dndioreply(
                orig_cmd='',
                status=True,
                dc_channel=msg.dc_channel,
                dc_user=msg.user,
                addtl_data=addtl_data,
                err_msg=''
            )
            #build the roll reply using the other reply objects
            resp = dndio_pb2.rollreply(
                common=c,
                dierolls=[r]
            )
            #return the response
            return resp
        except Exception as e:
            import traceback
            err_msg = await self.proc_err_msg(
                msg,
                'char set',
                ERR_MSGS['imp_err']+'\n{}: {}'.format(e,traceback.format_exc(e))
            )
            return err_msg

    async def roll_skill(self,msg):#,campaign,char,skill):
        try:
            args = json.loads(msg.args)
            campaign = msg.dc_channel # args['dc_channel']
            char= msg.user #args['user']
            skill=args['ability']

            #do we want to build a check for armor being worn on stealth checks? we have the data.
            char_query = """SELECT char_class,level,skills,str,wis,cha,con,int,dex,str from char_table where campaign_id='{}' and char_id='{}' allow filtering;""".format(
                campaign,char
            )
            skill_query = """SELECT modifier FROM skills where skill='{}'""".format(skill.lower())
            corr_id = str(uuid.uuid4())
            char_resp = await self.rmq_client.call(char_query,corr_id)
            char_resp = json.loads(char_resp)['rows'][0]
            logger.debug(char_resp)
            prof_query = "SELECT prof_bonus FROM classes WHERE class_id='{}-{}';".format(
                char_resp['char_class'],char_resp['level']                
            )
            corr_id = str(uuid.uuid4())
            skill_resp = await self.rmq_client.call(skill_query,corr_id)
            skill_resp = json.loads(skill_resp)['rows'][0]['modifier'].lower()
            corr_id = str(uuid.uuid4())
            prof_resp = await self.rmq_client.call(prof_query,corr_id)
            prof_resp = json.loads(prof_resp)['rows'][0]['prof_bonus']
            #this formula works to give the correct modifier for all stats
            stat_mod = (char_resp[skill_resp] - 10) // 2
            prof_bonus = prof_resp
            addtl_data=''
            adv = int(args.get('advantage',0) or 0)
            dadv = int(args.get('disadvantage',0) or 0)
            dice = 1+ adv+dadv
            roll = [random.randint(1,20) for i in range(dice)]
            mods = [stat_mod]
            mod_roll = [r+stat_mod for r in roll]
            if skill in char_resp['skills']:
                mod_roll = [r+prof_bonus for r in mod_roll]
                mods.append(prof_bonus)
                addtl_data+="You're proficient in {} checks, so you add your proficiency bonus {}\n".format(args['ability'],prof_bonus)
            addtl_data+='Your {} modifier is {}'.format(skill_resp.upper(),stat_mod)
            if adv > 0:
                total = max(mod_roll)
            elif dadv:
                total = min(mod_roll)
            else:
                total = max(mod_roll)
            #update to a message or some other format?
            c = dndio_pb2.dndioreply(
                orig_cmd='roll check {}'.format(args['ability']),
                status=True,
                dc_channel=msg.dc_channel,
                dc_user=msg.user,
                addtl_data=addtl_data,
                err_msg=''
            )
            r = dndio_pb2.roll(
                roll_type='{} check'.format(args['ability']),
                die_rolls=roll,
                modifiers=mods,
                modified_rolls=mod_roll,
                total = total
            )
            #build the roll reply using the other reply objects
            resp = dndio_pb2.rollreply(
                common=c,
                dierolls=[r]
            )
            #return the response
            return resp

        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                "roll skill",
                ERR_MSGS['imp_err'] + " " + str(e)
            )
            return err_msg

    async def proc_err_msg(self,msg,cmd,err_msg):
        logger.error(' [x] processing error message')
        common = dndio_pb2.dndioreply(
            orig_cmd=cmd,
            status=False,
            dc_channel=msg.dc_channel,
            dc_user=msg.user,
            err_msg=err_msg
        )
        return dndio_pb2.rollreply(
            common=common
        )

    def proc_success_msg(self,msg,cmd,addtl_data):
        return dndio_pb2.dndioreply(
            orig_cmd=cmd,
            status=True,
            dc_channel=msg.dc_channel,
            dc_user=msg.user,
            addtl_data=addtl_data
        )

    async def roll_spell_atk(self,msg):
        try:
            char_dat = await self.check_char_exists(msg)
            if not char_dat[0]:
                err_msg = await self.proc_err_msg(
                    msg,
                    'roll-spell-atk',
                    ERR_MSGS['no_char']
                )
            char_dat = char_dat[1]
            logger.debug(char_dat)
            args = json.loads(msg.args)
            logger.debug("[!!!!!] {}".format(args))
            spell = args['name']
            slot_lvl = int(args['level'][0])
            campaign = msg.dc_channel
            char = msg.user
            adv = int(args['advantage'])
            dadv = int(args['disadvantage'])
            cmd='roll-spell-atk'
            errors = []
            err_msg = ""
            ## add handlers here - if this isn't a spellcaster, or there's missing data in their char sheet, return immediately.
            if None in [char_dat['cha'],char_dat['wis'],char_dat['int']]:
                err_msg+= 'Your character is not fully initialized.\n'
                errors.append(True)
            for stat,val in {"CHA":char_dat['cha'],"WIS":char_dat['wis'],"INT":char_dat['int']}.items():
                if val is None:
                    err_msg+="{} is not set.\n".format(stat)

            if isinstance(char_dat['spellslots'],dict) and len(char_dat['spellslots'].keys()) == 0:
                errors.append(True)
                err_msg+="You do not have any spellslots.  Either your character is not yet initialized, or you're not a spellcaster.\n"
            if (
                slot_lvl > 0 and 
                isinstance(char_dat['spellslots'],dict) and 
                not char_dat['spellslots'].get(str(slot_lvl),0)
            ):
                    errors.append(True)
                    err_msg+="Your character does not have any available level {} spellslots. Your character's current spellslots are {}.\n".format(
                        slot_lvl,char_dat['spellslots']
                    )

            if char_dat['level'] is None:
                errors.append(True)
                err_msg+="Your character is not fully initialized. You need to have your character level set.\n"
            
            if char_dat['char_class'] is None:
                errors.append(True)
                err_msg+="Your character is not fully initialized. You need to have your character class set.\n"
            
            if spell not in char_dat['spells']:
                errors.append(True)
                err_msg+="Your character does not have {} in their known spells list.\n".format(spell)

            if True in errors:
                err_msg = await self.proc_err_msg(msg,cmd,err_msg)
                return err_msg

            class_st_query = """ 
            SELECT * FROM class_start WHERE char_class='{}'
            """.format(char_dat['char_class'])
            corr_id = str(uuid.uuid4())
            class_start_dat = await self.rmq_client.call(
                class_st_query,corr_id)
            class_start_dat = json.loads(class_start_dat)['rows'][0]

            if not class_start_dat.get('spell_atk_mod',False):
                err_msg = await self.proc_err_msg(
                    msg,
                    cmd,
                    "Your character is not a spellcaster, and cannot cast any spells."
                )
                return err_msg

            class_lvl_query = """ 
            SELECT prof_bonus FROM classes WHERE class_id='{}-{}'
            """.format(char_dat['char_class'],char_dat['level'])
            corr_id = str(uuid.uuid4())
            prof_bonus=await self.rmq_client.call(class_lvl_query,corr_id)
            prof_bonus = json.loads(prof_bonus)['rows'][0]['prof_bonus']

            modifiers = []

            ext_dice = adv+dadv

            rolls = [random.randint(1,20) for i in range(1+ext_dice)]
            
            spell_mod = (char_dat[class_start_dat['spell_atk_mod'].split('+')[1].lower()]-10)//2

            mod_rolls = [r+spell_mod+prof_bonus for r in rolls]

            # modifiers = [('prof_bonus',prof_bonus),(class_start_dat['spell_atk_mod'].split('+')[1].lower(),spell_mod)]
            modifiers = [prof_bonus,spell_mod]
            if adv>0:
                total = max(mod_rolls)
            elif dadv>0:
                total = min(mod_rolls)
            else:
                total = max(mod_rolls)
            
            r = dndio_pb2.roll(
                roll_type='spell attack: {}'.format(spell),
                die_rolls=rolls,
                modifiers=modifiers,
                modified_rolls=mod_rolls,
                total=total
            )

            c = self.proc_success_msg(msg,cmd,'')

            return dndio_pb2.rollreply(
                common=c,
                dierolls=[r]
            )
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                "roll spell atk",
                ERR_MSGS['imp_err'] + " " + str(e)
            )
            return err_msg

    async def roll_spell_dmg(self,spell,slot_lvl,campaign,char,msg):
        try:
            ##generate and populate queries
            char_query = """SELECT spells,spell_dc,spellslots from characters WHERE char_id='{}' and campaign_id='{}' allow filtering;""".format(
                char,campaign
            )
            spell_query = """SELECT * FROM spells where name='{}' allow filtering;""".format(spell)
            ## route queries to rmq db worker async & await response
            corr_id = str(uuid.uuid4())
            char_response = await self.rmq_client.call(char_query,corr_id)
            corr_id = str(uuid.uuid4())
            spell_response = await self.rmq_client.call(spell_query,corr_id)
            ## extract out the appropriate information...
            char_data = char_response['rows'][0]

            spell_data = spell_response['rows'][0]

            if spell['name'] not in char_data['spells']:
                msg = dndio_pb2.dndioreply(
                    orig_command='',
                    status=False,
                    dc_channel=campaign,
                    dc_user=char,
                    # err_msg='Your character does not have {} in its known spells list'.format(spell)
                )
                reply = dndio_pb2.rollreply(
                    common=msg
                )
                return reply
            if slot_lvl < spell_data['level']:
                pass #cant cast it - trying to cast at a lower slot level than the spell can be cast
                #craft a specialty return message
                msg = dndio_pb2.dndioreply(
                    orig_command='',
                    status=False,
                    dc_channel=campaign,
                    dc_user=char,
                    # err_msg='You cannot cast this spell with a slot below {}'.format(spell_data['level'])
                )
                reply = dndio_pb2.rollreply(
                    common=msg
                )
                return reply
                #add handler code here

            if char_data['spellslots'][slot_lvl] == 0:
                msg = dndio_pb2.dndioreply(
                    orig_command='',
                    status=False,
                    dc_channel=campaign,
                    dc_user=char,
                    # err_msg='You are out of level {} spellslots, and cannot cast at the requested level.'.format(slot_lvl)
                )
                reply = dndio_pb2.rollreply(
                    common=msg
                )
                return reply

            mult = spell_data['mult']
            hard_mod = spell_data['hard_mod']
            upcast = dict(spell_data['upcast'])
            dmg = spell_data['dmg']
            char_level = char_data['level']
            if len(upcast.keys()) > 0:
                upcast_lvl = list(upcast.keys())[0]
            else:
                upcast_lvl = 21
            if upcast_lvl <= slot_lvl:
                upcast_dice = slot_lvl-upcast_lvl + 1
            else:
                upcast_dice = 0
            lvls = [x for x in dmg.keys() if x <= char_level]
            lvls.sort()
            target_dmg = dmg.get(lvls[-1])
            results = {}
            mod_results = {}
            ### this section and below needs to be built better...
            ### need to eliminate the double-iteration of creating a dict
            ### and then converting to rolls and replies...
            for k,v in target_dmg.items():
                results[k] = []
                mod_results[k] = []
                for l,w in v[0].items(): # this may need to change...
                    for i in range(upcast_dice+(l*mult)):
                        roll = random.randint(1,w)
                        results[k].append(roll)
                        mod_results[k].append(roll+hard_mod)
            msgs = []
            for k,v in results.items():
                msgs.append(dndio_pb2.roll(
                    roll_type='spell',
                    die_rolls = [],
                    modifiers = [],
                    modified_rolls = [],
                    total = 0
                ))
            notes = ''
            if isinstance(spell_data['save'],str):
                #handler code here to include in additional data?
                notes = 'This spell requires a {} saving throw.  On a failed save, it has {}.  Your spellsave DC is: {}'.format(
                    spell_data['save'],spell_data['save_impact'],char_data['spell_DC']
                ) #save impacts = "no impact", "full damage", "other impact"
                if spell['save_impact'] == 'other':
                    notes+=''#other impact here...
                pass
            top = dndio_pb2.dndioreply(
                orig_command=msg.cmd + msg.subcmd + msg.args,
                status=True,
                dc_channel=campaign,
                dc_user=char,
                addtl_data=notes
            )
            reply = dndio_pb2.roll_reply(
                common=top,
                dierolls=msgs
            )
            return reply
        except Exception as e:
            err_msg = self.proc_err_msg(
                msg,
                "roll spell damage",
                ERR_MSGS['imp_err'] + " " + str(e)
            )
            return err_msg

    async def roll_atk(self,msg): #weapon,campaign,char,adv,disadv):
        ##right now - this takes 4 queries to make it work.
        #building a way to send all queries across and execute them
        #and package the results / send them back may be ideal.
        ## generate and populate queries
        try:
            args = json.loads(msg.args)
            char = msg.user
            campaign = msg.dc_channel #args['dc_channel']
            weapon = args['action']
            char_query = """SELECT * FROM char_table WHERE char_id='{}' and campaign_id='{}' allow filtering;""".format(
                char,campaign
            )
            corr_id = str(uuid.uuid4())
            chr_data = await self.rmq_client.call(char_query,corr_id)
            chr_data = json.loads(chr_data)['rows'][0]
            if weapon not in chr_data['equipped'].values(): #or weapon not in chr_data['weapons'] ?
                common = dndio_pb2.dndioreply(
                    orig_cmd='',
                    status=False,
                    dc_channel=campaign,
                    dc_user=char,
                    err_msg='You do not have {} equipped.  You currently have {} equipped as a weapon'.format(weapon,chr_data['equipped']['weapon'])
                )
                response = dndio_pb2.rollreply(
                    common=common
                )
                return response
            wep_query = """SELECT name,dmg,mod,subtype FROM weapons WHERE name='{}' allow filtering;""".format(weapon)
            corr_id = str(uuid.uuid4())
            wep_data = await self.rmq_client.call(wep_query,corr_id)
            wep_data = json.loads(wep_data)['rows'][0]
            prof_query = """SELECT proficiencies['weapon_class'] AS weapon_class,proficiencies['weapons'] AS weapons FROM class_start WHERE char_class='{}';""".format(chr_data['char_class'])
            class_query = """SELECT prof_bonus from classes  WHERE class_id = '{}';""".format(chr_data['char_class']+'-'+str(chr_data['level']))
            corr_id = str(uuid.uuid4())
            class_data = await self.rmq_client.call(class_query,corr_id)
            prof_bonus = json.loads(class_data)['rows'][0]['prof_bonus']
            corr_id = str(uuid.uuid4())
            proficiencies = await self.rmq_client.call(prof_query,corr_id)
            proficiencies=json.loads(proficiencies)['rows'][0]
            modifiers = []
    #         logger.info("""
    #  [!!!!!!] \nchar_data: {}\nweapon data: {}\nproficiency_bonus: {}\nproficiencies: {}                    
    # """.format(chr_data,wep_data,prof_bonus,proficiencies))
            addtl_data = ''

            if args['advantage']:
                add = int(args['advantage'])
            elif args['disadvantage']:
                add = int(args['disadvantage'])
            else:
                add = 0
            rolls = [random.randint(1,20) for i in range(1+add)]
            
            mod_rolls = rolls.copy()
            #if the char is proficient in the weapon or class of weapons - add proficiency bonus.
            for k,v in proficiencies.items():
                if v is None:
                    proficiencies[k] = []
            if wep_data['name'] in proficiencies['weapons'] or wep_data['subtype'] in proficiencies['weapon_class']:
                #character type is proficient in the given weapon type
                mod_rolls = [m+prof_bonus for m in mod_rolls]
                modifiers.append(prof_bonus)
                addtl_data+="You're proficient with {}, and you add your proficiency bonus ({})\n".format(
                    wep_data['name'],prof_bonus
                )
            
            #determine if STR or DEX is the maximum modifier
            #and which is available based on the weapon
            add_mods = []
            for m in wep_data['mod']:
                add_mods.append((m,(chr_data[m.lower()]-10)//2))
                
            add_mod = max(add_mods,key=lambda x: x[1])
            modifiers.append(add_mod[1])
            addtl_data+='Your {} modifier is {}.\n'.format(add_mod[0],add_mod[1])
            if add_mod[0]=='DEX':
                addtl_data+="Your DEX modifier is used because this weapon has finesse, and your DEX modifier is higher than your STR.\n"
            #increment modified rolls based on max value
            mod_rolls = [m+add_mod[1] for m in mod_rolls]

            #extract the "total" based on advantage/disadvantage
            if args['advantage']:
                total = max(mod_rolls)
            if args['disadvantage']:
                total = min(mod_rolls)
            if not args['advantage'] or args['disadvantage']:
                total = max(mod_rolls)
            
            r = dndio_pb2.roll(
                roll_type='Attack: {}'.format(args['action']),
                die_rolls=rolls,
                modifiers=modifiers,
                modified_rolls=mod_rolls,
                total = total
            )
            c = dndio_pb2.dndioreply(
                orig_cmd='',
                status=True,
                dc_channel=msg.dc_channel,
                dc_user=msg.user,
                addtl_data=addtl_data,
                err_msg=''
            )
            #build the roll reply using the other reply objects
            resp = dndio_pb2.rollreply(
                common=c,
                dierolls=[r]
            )
            #return the response
            return resp
        except Exception as e:
            err_msg = self.proc_err_msg(
                msg,
                "roll attack",
                ERR_MSGS['imp_err'] + " " + str(e)
            )
            return err_msg

    async def roll_atk_dmg(self,msg):#weapon,campaign,char,num_hands,adv,disadv):
        try:
            #extract pertinent arguments from the message
            args = json.loads(msg.args)['action']
            num_hands = 1 #need a handler in the parser
            weapon = args
            char = msg.user
            campaign = msg.dc_channel
            #####
            #initialize a query to assess the character
            corr_id = str(uuid.uuid4())
            char_query = """SELECT * from char_table WHERE char_id='{}' and campaign_id='{}' allow filtering;""".format(
                char,campaign
            )
            chr_data = await self.rmq_client.call(char_query,corr_id)
            chr_data = json.loads(chr_data)['rows'][0]
            #make sure the weapon is equipped.
            if weapon not in chr_data['equipped'].values(): #weapon not in chr_data['weapons'] or
                if chr_data['equipped'].get('weapon') is not None:
                    err_msg = 'You do not have {} equipped.  You currently have {} equipped as a weapon'.format(weapon,chr_data['equipped']['weapon'])
                elif chr_data['equipped'] is None and len(chr_data['weapons']) > 0:
                    err_msg = 'You do not have any weapons equipped.  Please equip a weapon from your inventory: {}\nAlternatively, you can roll an unarmed strike with (flag).'.format(
                        chr_data['weapons']
                    )
                elif len(chr_data['weapons']) == 0:
                    err_msg = 'You do not have any weapons equipped or in your inventory.  You can only perform unarmed strike attacks with (flag).'
                common = dndio_pb2.dndioreply(
                    orig_cmd='',
                    status=False,
                    dc_channel=campaign,
                    dc_user=char,
                    err_msg=err_msg
                )
                response = dndio_pb2.rollreply(common=common)
                return response
            wep_query = """SELECT * FROM weapons WHERE name='{}' allow filtering;""".format(weapon)
            corr_id = str(uuid.uuid4())
            wep_data = await self.rmq_client.call(wep_query,corr_id)
            wep_data = json.loads(wep_data)['rows'][0]
            modifiers = []
            add_mods = []
            for m in wep_data['mod']:
                if not chr_data.get(m.lower()):
                    #char not fully initialized
                    err_msg = "You do not have your character fully initialized.  {} is not set for your character.\n".format(m.upper())
                else:
                    add_mods.append((m,(chr_data[m.lower()]-10)//2))
            if len(add_mods) > 0:
                add_mod = max(add_mods,key=lambda x: x[1])
            else:
                add_mod = 0
            modifiers.append(add_mod[1])
            rolls = []
            logger.debug(wep_data['dmg'])
            for dmg_type,dmg_dice in wep_data['dmg'][str(num_hands)+'hnd'].items():
                logger.debug("{}".format(dmg_type,dmg_dice))
                for num_dice,dice_size in dmg_dice.items():
                    roll = [random.randint(1,int(dice_size)) for i in range(int(num_dice))]
                    mod_roll = [r+add_mod[1] for r in roll]
                    r = dndio_pb2.roll(
                            roll_type='dmg-{}'.format(dmg_type),
                            die_rolls = roll,
                            modifiers = [add_mod[1]],
                            modified_rolls = mod_roll,
                            total = sum(mod_roll)
                    )
                    rolls.append(r)
            c = dndio_pb2.dndioreply(
                orig_cmd='',
                status=True,
                dc_channel=msg.dc_channel,
                dc_user=msg.user,
                addtl_data='',
                err_msg=''
            )
            reply = dndio_pb2.rollreply(
                common=c,
                dierolls=rolls
            )
            return reply
        except Exception as e:
            err_msg = await self.proc_err_msg(
                msg,
                "roll attack damage",
                ERR_MSGS['imp_err'] + " " + str(e)
            )
            return err_msg

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
                    logger.debug(msg.body)
                    logger.debug(inbound_msg.subcmd)
                    logger.info("  [x] Parsed RPC to GRPC, converting to query")
                    ##### HERE'S WHERE WE'LL PARSE THE MESSAGE FROM THE CLIENT
                    ## AND USE THAT TO CRAFT DIFFERENT QUERIES
                    ## the parsed command gets fed to one of the above roll_ functions
                    ## and it will handle the query routing and response
                    ## each will return a response to this function, and this function
                    ## will send the final message.
                    funcs = {
                        'initiative':self.roll_initiative,
                        'attack':self.roll_atk,
                        'save':self.roll_save,
                        # 'skill':self.roll_skill,
                        'spell':self.roll_spell_atk,
                        'raw':self.roll_raw,
                        'damage':self.roll_atk_dmg,
                        'check':self.roll_check
                    }
                    func = funcs[inbound_msg.subcmd]
                    # loop = asyncio.get_running_loop()
                    # task = loop.create_task(func(inbound_msg))
                    # reply = await task
                    reply = await func(inbound_msg)
                    # # rep = dndio_pb2.rollreply()
                    # rep = reply#.copy()
                    await self.exchange.publish(
                        Message(
                            body=reply.SerializeToString(),
                            correlation_id=msg.correlation_id,
                            expiration=5000
                        ),
                        routing_key=msg.reply_to
                    )
                    logging.info(' [x] Processed Request')
                except Exception as e:
                    logging.exception(" [!] Error processing for message: {}".format(msg))
                    inbound_msg = dndio_pb2.dndiomsg()
                    inbound_msg.ParseFromString(msg.body)
                    err_msg = await self.proc_err_msg(
                        inbound_msg,
                        "run",
                        ERR_MSGS['imp_err'] + " " + str(e)
                    )
                    await self.exchange.publish(
                        Message(
                            body=err_msg.SerializeToString(),
                            correlation_id=msg.correlation_id
                        ),
                        routing_key=msg.reply_to
                    )


if __name__=='__main__':
    worker = rmq_server("amqp://guest:guest@{}:{}".format(RMQ_HOST,RMQ_PORT),'grpc.workerroll')
    asyncio.run(worker.run())