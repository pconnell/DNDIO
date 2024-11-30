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
import workerRoll_pb2, workerRoll_pb2_grpc
import dndio_pb2, dndio_pb2_grpc
import random 
##################################################################

##################################################################
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

    async def roll_spell(self,spell,slot_lvl,campaign,char):
        qs = []
        qs.append(QUERIES.get('get_char').format(char,campaign))
        # qs.append(QUERIES.get('get_char_map').format(char,campaign))
        qs.append(QUERIES.get('get_class'))
        qs.append(QUERIES.get('get_spells'))
        #forward the queries over to db worker
        #use await...
        #get the response
        #roll the dice
        #craft a protobuf message
        #return the result to RMQ via return statement
        ## this gets called from run!
        pass

    async def roll_initiative(self,msg,campaign,char):
        #should be good to go!
        char_query = """SELECT DEX from characters where campaign_id={} and char_id={} allow filtering;""".format(
            campaign,char
        )
        char_resp = await self.rmq_client.call(char_query)['rows'][0]['DEX']
        mod = char_resp #do some math here...
        if msg.adv or msg.dadv:
            rolls = [random.randint(1,20) for i in range(2)]
        else:
            rolls = [random.randint(1,20)]
        mod_rolls = [r+mod for r in rolls]
        if msg.adv:
            total = [max(mod_rolls)]
        elif msg.dadv:
            total = [min(mod_rolls)]
        else:
            total = mod_rolls.copy()

        return (rolls,mod_rolls,total)

    async def roll_save(self,msg,campaign, char, stat):
        
        char_query = """SELECT char_class,{},save_throws from characters where campaign_id={} and char_id={} allow filtering;""".format(
            stat.lower(),campaign,char
        )
        # class_query = """ 
        #     SELECT prof_bonus FROM classes WHERE class_id='{}'
        # """.format()
        char_resp = await self.rmq_client.call(char_query,msg.correlation_id)['rows'][0]
        mod = (char_resp[stat]-10)//2 #do some math to get the modifier
        class_st_query = """SELECT proficiencies['Saving Throws'] FROM class_start WHERE char_class='{}'"""
        class_query = """SELECT * FROM classes WHERE class_id='{}';""".format(
            char_resp['char_class'] + '-' + str(char_resp['level'])
        )
        class_st_resp = await self.rmq_client.call(class_st_query,msg.correlation_id)['rows'][0]
        class_resp = await self.rmq_client.call(class_query,msg.correlation_id)['rows'][0]
        modifiers = []
        modifiers.append((stat,mod))
        if msg.adv or msg.dadv: #update modify to be correct...
            roll = [random.randint(1,20) for i in range(2)]
        else:
            roll = [random.randint(1,20)]
        if stat in class_st_resp:
            modifiers.append(('prof_bonus',class_resp['prof_bonus']))
            mod_roll= [r+class_resp['prof_bonus']+mod for r in roll]#char_resp['prof_bonus']+mod
        else:
            mod_roll+=[r+mod for r in roll]
        if msg.adv:
            total = [max(mod_roll)]
        elif msg.dadv:
            total = [min(mod_roll)]
        else:
            total = mod_roll.copy()
        #update to a message or some other format?
        return {
            'rolls':roll,
            'mod_rolls':mod_roll,
            'modifiers':modifiers,
            'total':total
        }

    async def roll_skill(self,msg,campaign,char,skill):
        #do we want to build a check for armor being worn on stealth checks? we have the data.
        char_query = """SELECT {},skills,str,wis,cha,con,int,dex,str prof_bonus from characters where campaign_id={} and char_id={} allow filtering;""".format(
            skill.lower(),campaign,char
        )
        skill_query = """SELECT modifier FROM skills where name={}""".format(skill.lower())
        char_resp = await self.rmq_client.call(char_query,msg.correlation_id)['rows'][0]
        skill_resp = await self.rmq_client.call(skill_query,msg.correlation_id)['rows'][0]['modifier'].lower()
        #this formula works to give the correct modifier for all stats
        mod = (char_resp[skill_resp] - 10) // 2
        if msg.adv or msg.dadv: #update modify to be correct...
            roll = [random.randint(1,20) for i in range(2)]
        else:
            roll = [random.randint(1,20)]
        if skill in char_resp['skills']:
            mod_roll= [r+char_resp['prof_bonus']+mod for r in roll]
        else:
            mod_roll+=[r+mod for r in roll]
        if msg.adv:
            total = [max(mod_roll)]
        elif msg.dadv:
            total = [min(mod_roll)]
        else:
            total = mod_roll.copy()
        #update to a message or some other format?
        return (roll,mod_roll,total)

    async def roll_spell_atk(self,msg,spell,slot_lvl,campaign,char):
        char_query = """ 
        SELECT spells,spellslots,chr,wis,int FROM char_table 
        WHERE user_id='{}' AND campaign_id='{}'
        """.format(char,campaign)
        char_dat = await self.rmq_client.call(char_query,msg.correlation_id)['rows'][0]

        ## add handlers here - if this isn't a spellcaster, or there's missing data in their char sheet, return immediately.

        if char_query['spellslots'] = {}
            return Message(
                #you're note a spellcaster
            )

        # if char_dat['spell_dc'] is None:
        #     return Message(
        #         #need a spellsave dc
        #     )
        if None in [char_dat['chr'],char_dat['wis'],char_dat['int']:
            return Message(
                #need stats to be set
            )

        if char_dat['level'] is None:
            return Message(
                #need level to be set.
            )
        
        if char_dat['char_class'] is None:
            return Message(
                #need class to be set
            )
        
        if spell not in char_dat['spells']:
            return Message(
                #you don't know the spell
            )

        class_st_query = """ 
        SELECT * FROM class_start WHERE char_class='{}'
        """.format(char_dat['char_class'])
        class_start_dat = await self.rmq_client.call(class_st_query,msg.correlation_id)['rows'][0]

        class_lvl_query = """ 
        SELECT prof_bonus FROM classes WHERE class_id='{}-{}'
        """.format(char_dat['char_class'],char_dat['level'])

        prof_bonus=await self.rmq_client.call(class_lvl_query,msg.correlation_id)['rows'][0]['prof_bonus']

        modifiers = []

        if msg.adv or msg.disadv:
            rolls = [random.randint(1,20) for i in range(2)]
        else:
            rolls = [random.randint(1,20)]
        
        spell_mod = (char_query[class_start_dat['spell_atk_mod'].split('+')[1].lower()]-10)//2

        mod_rolls = [r+spell_mod+prof_bonus for r in rolls]

        modifiers = [('prof_bonus',prof_bonus),(class_start_dat['spell_atk_mod'].split('+')[1].lower(),spell_mod)]

        if msg.adv:
            total = max(mod_rolls)
        elif msg.disadv:
            total = min(mod_rolls)
        else:
            total = max(mod_rolls)
        
        return {
            'roll_type':'spell-attack',
            'rolls':rolls,
            'mod_rolls':mod_rolls,
            'total':total
        }

    async def roll_spell_dmg(self,spell,slot_lvl,campaign,char,msg):
        ##generate and populate queries
        char_query = """SELECT spells,spell_dc,spellslots from characters WHERE char_id='{}' and campaign_id='{}' allow filtering;""".format(
            char,campaign
        )
        spell_query = """SELECT * FROM spells where name='{}' allow filtering;""".format(spell)
        ## route queries to rmq db worker async & await response
        char_response = await self.rmq_client.call(char_query,msg.correlation_id)
        spell_response = await self.rmq_client.call(spell_query,msg.correlation_id)
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

    async def roll_atk(self,weapon,campaign,char,adv,disadv):
        ##right now - this takes 4 queries to make it work.
        #building a way to send all queries across and execute them
        #and package the results / send them back may be ideal.
        ## generate and populate queries
        char_query = """SELECT * from char_table WHERE char_id='{}' and campaign_id='{}' allow filtering;""".format(
            char,campaign
        )
        chr_data = await self.rmq_client.call(char_query)['rows'][0]
        if weapon not in chr_data['weapons'] or weapon not in chr_data['equipped']:
            response = dndio_pb2.dndioreply(
                orig_command='',
                status=False,
                dc_channel=campaign,
                dc_user=char,
                addtl_data='You do not have {} equipped.  You currently have {} equipped as a weapon'.format(weapon,chr_data['?'])
            )
            return response
        wep_query = """SELECT * FROM weapons WHERE name='{}' allow filtering;""".format(weapon)
        wep_data = await self.rmq_client.call(wep_query)['rows'][0]
        prof_query = """SELECT proficiencies['weapon_class'] AS weapon_class,proficiencies['weapons'] AS weapons FROM class_start WHERE char_class='{}';""".format(chr_data['char_class'])
        class_query = """SELECT * from classes WHERE class_id = {};""".format(chr_data['char_class']+'-'+str(chr_data['level']))
        class_data = await self.rmq_client.call(class_query)['rows'][0]
        prof_bonus = class_data['prof_bonus']
        proficiencies = await self.rmq_client.call(prof_query)['rows'][0]
        if adv or disadv:
            rolls = [random.randint(1,20) for i in range(2)]
        else:
            rolls = [random.randint(1,20)]
        
        mod_rolls = rolls.copy()
        #if the char is proficient in the weapon or class of weapons - add proficiency bonus.
        if wep_data['name'] in proficiencies['weapons'] or wep_data['subtype'] in proficiencies['weapon_class']:
            #character type is proficient in the given weapon type
            mod_rolls = [m+prof_bonus for m in mod_rolls]
        
        #determine if STR or DEX is the maximum modifier
        #and which is available based on the weapon
        add_mods = []
        for m in wep_data['mod']:
            add_mods.append((m,(chr_data[m.lower()]-10)//2))
        add_mod = max(add_mods,key=lambda x: x[1])

        #increment modified rolls based on max value
        mod_rolls = [m+add_mod[1] for m in mod_rolls]

        #extract the "total" based on advantage/disadvantage
        if adv:
            total = [max(mod_rolls)]
        if disadv:
            total = [min(mod_rolls)]
        if not adv or disadv:
            total = [max(mod_rolls)]
        return {
            'rolls':rolls,
            'mod_rolls':mod_rolls,
            'modifiers':[add_mods,],
            'total':total
        }

    async def roll_atk_dmg(self,weapon,campaign,char,num_hands,adv,disadv):
        char_query = """SELECT * from char_table WHERE char_id='{}' and campaign_id='{}' allow filtering;""".format(
            char,campaign
        )
        chr_data = await self.rmq_client.call(char_query)['rows'][0]
        if weapon not in chr_data['weapons'] or weapon not in chr_data['equipped']:
            response = dndio_pb2.dndioreply(
                orig_command='',
                status=False,
                dc_channel=campaign,
                dc_user=char,
                addtl_data='You do not have {} equipped.  You currently have {} equipped as a weapon'.format(weapon,chr_data['?'])
            )
            return response
        wep_query = """SELECT * FROM weapons WHERE name='{}' allow filtering;""".format(weapon)
        wep_data = await self.rmq_client.call(wep_query)['rows'][0]
        add_mods = []
        for m in wep_data['mod']:
            add_mods.append((m,chr_data[m.lower()]))
        add_mod = max(add_mods,key=lambda x: x[1])

        dmg_rolls = {'base':{},'modified':{},'total':0}
        for hands,dmgs in wep_data['dmg'][str(num_hands)+'-hnd']:
            for dmg_type, dmg_dice in dmgs.items():
                for num_dice,dice_size in dmg_dice.items():
                    rolls = [random.randint(1,dice_size) for i in range(num_dice)]
                    dmg_rolls['base'][dmg_type] = rolls
                    dmg_rolls['modified'][dmg_type] = [r+add_mod[1] for r in rolls]
                    dmg_rolls['total']+= sum(dmg_rolls('modified'))
        dmg_rolls['modifier'] = add_mod
        return dmg_rolls

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
                    
                    inbound_msg = workerRoll_pb2.msg()
                    inbound_msg.ParseFromString(msg.body)
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
                        'skill':self.roll_skill,
                        'spell':self.roll_spell
                    }
                    func = funcs[inbound_msg.cmd]
                    reply = await func(inbound_msg)
                    # query = "INSERT INTO worker (id,cmd,num) VALUES (uuid(),'{}',{})".format(
                    #     inbound_msg.cmd,
                    #     inbound_msg.num
                    # )
                    # logger.info(f"  [x] Query generated {query}, sending to db worker...")
                    # response = await self.rmq_client.call(query,msg.correlation_id)
                    # async with response:
                    # response = json.loads(response.decode())
                    # logger.info("  [x] Response to query received: {}".format(response))
                    # if response['success']:
                    #     reply = workerRoll_pb2.msgreply(
                    #         response = "Command {} with num {} successful! ({})".format(
                    #             inbound_msg.cmd,
                    #             inbound_msg.num,
                    #             json.dumps(response)
                    #         ),
                    #         outcome=True
                    #     )
                    # else:
                    #     reply = workerRoll_pb2.msgreply(
                    #         response = "Command {} with num {} failed!: {}".format(
                    #             inbound_msg.cmd,
                    #             inbound_msg.num,
                    #             json.dumps(response)
                    #         ),
                    #         outcome=False
                    #     )
                    await self.exchange.publish(
                        Message(
                            body=reply.SerializeToString(),
                            correlation_id=msg.correlation_id
                        ),
                        routing_key=msg.reply_to
                    )
                    logging.info(' [x] Processed Request')
                except Exception:
                    logging.exception(" [!] Error processing for message: {}".format(msg))


if __name__=='__main__':
    worker = rmq_server("amqp://guest:guest@{}:{}".format(RMQ_HOST,RMQ_PORT),'grpc.workerroll')
    asyncio.run(worker.run())