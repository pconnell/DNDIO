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
# import workerRoll_pb2, workerRoll_pb2_grpc
import dndio_pb2, dndio_pb2_grpc
import random 
from argparse import Namespace
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

    async def roll_spell(self,msg):
        pass

    async def roll_raw(self,msg):
        args = json.loads(msg.args)
        rolls = []
        if args.get('advantage') or args.get('disadvantage'):
            add = max([args.get('advantage'),args.get('disadvantage'),0])
            for k,v in args['rolls'].items():
                r = [random.randint(1,int(k)) for i in range(int(v)+int(add))]
                if args.get('disadvantage'):
                    tot = min(r)
                else:
                    tot = max(r)
                rolls.append(
                    dndio_pb2.roll(
                        roll_type='raw',
                        die_rolls=r,
                        modifiers=None,
                        modified_rolls=None,
                        total = tot
                    )
                )
        else:
            rolls = []
            for k,v in args['rolls'].items():
                r = [random.randint(1,int(k)) for i in range(int(v))]
                if args.get('disadvantage'):
                    tot = min(r)
                else:
                    tot = max(r)
                rolls.append(
                    dndio_pb2.roll(
                        roll_type='raw',
                        die_rolls=r,
                        modifiers=None,
                        modified_rolls=None,
                        total = tot
                    )
                )
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
        logger.info("  [x] roll reply: {}".format(roll_reply))
        await asyncio.sleep(.1)
        return roll_reply

    async def roll_initiative(self,msg):
        ### still need to handle advantage/disadvantage, subcmd vs cmd vs args...
        args = json.loads(msg.args)
        char_query = """SELECT dex from char_table where campaign_id='{}' and char_id='{}' allow filtering;""".format(
            msg.dc_channel,msg.user
        )
        
        corr_id = str(uuid.uuid4())
        char_resp = await self.rmq_client.call(char_query,corr_id)
        char_resp = json.loads(char_resp)
        dex_mod = char_resp['rows'][0]['dex']
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
            total = [max(mod_rolls)]
        elif args['disadvantage']:
            total = [min(mod_rolls)]
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
            orig_cmd='',
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
    
    async def roll_save(self,msg):#,campaign, char, stat):
        args = json.loads(msg.args)
        stat = ','.join(args['ability']).lower()
        campaign = msg.dc_channel
        char=msg.user
        char_query = """SELECT char_class,level,{} from char_table where campaign_id='{}' and char_id='{}' allow filtering;""".format(
            stat.lower(),campaign,char
        )
        corr_id = str(uuid.uuid4())
        char_resp = await self.rmq_client.call(char_query,corr_id)
        char_resp = json.loads(char_resp)['rows'][0]
        ability_mod = (char_resp[stat]-10)//2 #do some math to get the modifier


        class_st_query = """SELECT proficiencies['Saving Throws'] FROM class_start WHERE char_class='{}'""".format(char_resp['char_class'],char_resp['level'])
        class_query = """SELECT prof_bonus FROM classes WHERE class_id='{}';""".format(
            char_resp['char_class'] + '-' + str(char_resp['level'])
        )
        class_st_resp = await self.rmq_client.call(class_st_query,corr_id)
        class_st_resp = json.loads(class_st_resp)['rows'][0]
        proficiencies = class_st_resp['proficiencies__Saving_Throws']
        logger.info(" [!!!] {}".format(proficiencies,))
        class_resp = await self.rmq_client.call(class_query,corr_id)
        class_resp = json.loads(class_resp)['rows'][0]
        logger.info(" [!!!] {}\t{}".format(proficiencies,class_resp))
        # mod = class_resp['prof_bonus']
        addtl_data = ""
        modifiers = []
        modifiers.append(ability_mod)
        if args['advantage']:
            add = int(args['advantage'])
        elif args['disadvantage']:
            add = int(args['disadvantage'])
        else:
            add = 0
        roll = [random.randint(1,20) for i in range(1+add)]
        mod_roll = []
        if stat.upper() in proficiencies:
            addtl_data+= "You're proficient in {} saves - so you add your proficiency bonus ({})\n".format(
                stat.upper(),
                class_resp['prof_bonus']
            )
            modifiers.append((class_resp['prof_bonus']))
            mod_roll= [r+class_resp['prof_bonus']+ability_mod for r in roll]#char_resp['prof_bonus']+mod
        else:
            mod_roll+=[r+ability_mod for r in roll]
        if args['advantage']:
            total = max(mod_roll)
        elif args['disadvantage']:
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

    async def roll_skill(self,msg):#,campaign,char,skill):
        args = json.loads(msg.args)
        campaign = args['dc_channel']
        char=args['user']
        skill=args['skill']

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

        if isinstance(char_query['spellslots'],dict) and len(char_query['spellslots'].keys()) == 0:
            return Message(
                #you're note a spellcaster
            )

        # if char_dat['spell_dc'] is None:
        #     return Message(
        #         #need a spellsave dc
        #     )
        if None in [char_dat['chr'],char_dat['wis'],char_dat['int']]:
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

    async def roll_atk(self,msg): #weapon,campaign,char,adv,disadv):
        ##right now - this takes 4 queries to make it work.
        #building a way to send all queries across and execute them
        #and package the results / send them back may be ideal.
        ## generate and populate queries
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
        addtl_data+='Your {} modifier is {}.\n'.format(add_mod[0],add_mod[1])
        if add_mod[0]=='DEX':
            addtl_data+="Your DEX modifier is used because this weapon has finesse.\n"
            modifiers.append(add_mod[1])
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

    async def roll_atk_dmg(self,msg):#weapon,campaign,char,num_hands,adv,disadv):
        args = json.loads(msg.args)['action']
        num_hands = 1 #need a handler in the parser
        weapon = args
        char = msg.user
        campaign = msg.dc_channel
        corr_id = str(uuid.uuid4())
        char_query = """SELECT * from char_table WHERE char_id='{}' and campaign_id='{}' allow filtering;""".format(
            char,campaign
        )
        chr_data = await self.rmq_client.call(char_query,corr_id)
        chr_data = json.loads(chr_data)['rows'][0]
        if weapon not in chr_data['equipped'].values(): #weapon not in chr_data['weapons'] or
            common = dndio_pb2.dndioreply(
                orig_cmd='',
                status=False,
                dc_channel=campaign,
                dc_user=char,
                err_msg='You do not have {} equipped.  You currently have {} equipped as a weapon'.format(weapon,chr_data['equipped']['weapon'])
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
            add_mods.append((m,(chr_data[m.lower()]-10)//2))
        add_mod = max(add_mods,key=lambda x: x[1])
        modifiers.append(add_mod[1])

        rolls = []
        logger.info(wep_data['dmg'])
        for dmg_type,dmg_dice in wep_data['dmg'][str(num_hands)+'hnd'].items():
            logger.info("{}".format(dmg_type,dmg_dice))
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
            # for dmg_type,dmg_dice in dmgs.items():
            #     logger.info("{} {}".format(dmg_type,dmg_dice))
            #     for num_dice,dice_size in dmg_dice.items():
            #         roll = [random.randint(1,dice_size) for i in range(num_dice)]
            #         mod_roll = [r+add_mod[1] for r in rolls]
            #         r = dndio_pb2.roll(
            #             roll_type='dmg-{}'.format(dmg_type),
            #             die_rolls = roll,
            #             modifiers = [add_mod[1]],
            #             modified_rolls = mod_roll,
            #             total = sum(mod_roll)
            #         )
            #         rolls.append(r)
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
        # dmg_rolls = {'base':{},'modified':{},'total':0}
        # for hands,dmgs in wep_data['dmg'][str(num_hands)+'-hnd']:
        #     for dmg_type, dmg_dice in dmgs.items():
        #         for num_dice,dice_size in dmg_dice.items():
        #             rolls = [random.randint(1,dice_size) for i in range(num_dice)]
        #             dmg_rolls['base'][dmg_type] = rolls
        #             dmg_rolls['modified'][dmg_type] = [r+add_mod[1] for r in rolls]
        #             dmg_rolls['total']+= sum(dmg_rolls('modified'))
        # dmg_rolls['modifier'] = add_mod
        # return dmg_rolls

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
                    logger.info(msg.body)
                    logger.info(inbound_msg.subcmd)
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
                        'spell':self.roll_spell,
                        'raw':self.roll_raw,
                        'damage':self.roll_atk_dmg
                    }
                    func = funcs[inbound_msg.subcmd]
                    reply = await func(inbound_msg)
                    # if inbound_msg.subcmd == 'raw':
                    #     reply = func(inbound_msg)
                    # else:
                    #     reply = await func(inbound_msg)
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

                    #################################################
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
                    # return reply


if __name__=='__main__':
    worker = rmq_server("amqp://guest:guest@{}:{}".format(RMQ_HOST,RMQ_PORT),'grpc.workerroll')
    asyncio.run(worker.run())