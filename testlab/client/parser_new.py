import argparse,shlex
'''
Parser: Defines the arguments passed by the client to the ingress controller.

We will also need to translate these from the Discord command itself passed to the bot.
'''

parser = argparse.ArgumentParser(prog='dndio')

subparsers = parser.add_subparsers(
    help='subcommand help'
)

##########################################################################
parser_init = subparsers.add_parser('init',help='channel initialization')
##########################################################################

##########################################################################
#                          Character Commands                            #
##########################################################################

parser_char = subparsers.add_parser('char',help='Character Commands')

char_sub = parser_char.add_subparsers(help='/char Subcommands')

# /char get commands
# e.g., dndio char get -b ability
get_sub = char_sub.add_parser("get", 
                              help="Get a piece of information from your, another player's, or an NPC's character sheet.",
                              aliases=['get'])

get_sub.add_argument("info", 
                     choices=['ability', 'skills', 'combat', 'equipped', 'inv', 'spellmod', 'spells', 'all'], nargs="*", default='all',
                     help='''
                     The type of information you want to pull from the character sheet.
                                          
                     Choices:
                     - ability:     Ability Scores
                     - skills:      Skills and Proficiencies
                     - combat:      HP, AC, and Initiative
                     - equipped:    Currently Equipped Items
                     - inv:         Inventory
                     - spellmod:    Spell Slots and Modifiers
                     - spells:      Known Spells
                     - all:         All Character Sheet Information
                     '''
                     )

get_sub.add_argument("-b", "--base", action='store_true', 
                     help='Get the base stat as it appears on the character sheet.',
                     default=False)

get_sub.add_argument("-c", "--char", default=None,
                     help="The name or numerical ID of the character to look up. Defaults to the player sending the command."
                     )

##########################################################################
#                     Set Character Info Commands                        #
##########################################################################
char_set = char_sub.add_parser('set', 
                               help="Modify a value on your, another player's, or an NPC's character sheet.", 
                               aliases=['set'])
set_sub = char_set.add_subparsers()

# Set ability score
# dndio char set ability STR 17
ability_sub = set_sub.add_parser('ability')

ability_sub.add_argument("score", choices=['CHA', 'STR', 'INT', 'WIS', 'DEX', 'CON'], nargs="+")
ability_sub.add_argument("value", type=int)

# Set skills
skill_sub = set_sub.add_parser('skills')
skill_sub.add_argument('skill', choices=['''Populate this later'''])

char_set.add_argument('-p','--prof_bonus',action='store')
char_set.add_argument('-a','--ac',action='store')
char_set.add_argument('-c','--class',action='store')
char_set.add_argument('-r','--race',action='store')
char_set.add_argument('-l','--level',action='store')
char_set.add_argument('-n','--name',action='store')
char_set.add_argument('-e','--equip',action='store')
char_set.add_argument('-g','--spells',metavar='KEY=VALUE',action='append')
char_set.add_argument('-q','--spellslots',metavar='KEY=VALUE',action='append')
char_set.add_argument('-w','--weapons',metavar='KEY=VALUE',action='append')
##########################################################################

#examples
def parse_str(s):
    print(s)
    print(parser.parse_args(shlex.split(s)))
    print('*'*80)



parse_str("char get -b ability")

# parse_str("""char set -s STR=11 -s DEX=18 -s CON=14 -s INT=12 -s WIS=12 -s CHR=20 
#     -p 3 
#     -a 16 
#     -c Sorcerer 
#     -r Autognome 
#     -l 7 
#     -n Melinda"""
# )
# parse_str('char set -k Insight=4 -k Persuasion=8 -k Arcana=3 -k Religion=4')
# parse_str("char set -w add='short sword' -w add='dagger' -w remove='compound bow'")
# parse_str('char set -e sword')
# parse_str("""char set 
#           -g 'Mending'=0 
#           -g 'Prestidigitation'=0 
#           -g 'Shape Water'=0 
#           -g 'Aid'=2 
#           -g 'Scorching Ray'=2 
#           -g 'Dispell Magic'=3 
#           -g 'Fireball'=3 
#           -g 'Summon Construct'=4
# """)



##########################################################################
# parser_lookup = subparsers.add_parser('lookup',help='lookup help')
# lookup_sub = parser_lookup.add_subparsers(help='lookup commands')


# lookup_spells = lookup_sub.add_parser('spells',help='spell search')
# lookup_spells.add_argument('-s','--school',action='store')
# lookup_spells.add_argument('-c','--class',action='store')
# lookup_spells.add_argument('-l','--level',action='store')
# lookup_spells.add_argument('-t','--conc',action='store_true')
# lookup_spells.add_argument('-v','--save',action='store_true')

# lookup_weapons = lookup_sub.add_parser('weapons',help='weapon search')
# lookup_weapons.add_argument('-w','--weight',action='store')
# lookup_weapons.add_argument('-p','--price',action='store')
# lookup_weapons.add_argument('-n','--name',action='store')

# lookup_armor = lookup_sub.add_parser('armor',help='armor search')
# lookup_armor.add_argument('-w','--weight',action='store')
# lookup_armor.add_argument('-p','--price',action='store')
# lookup_armor.add_argument('-n','--name',action='store')
##########################################################################

##########################################################################
# parser_roll = subparsers.add_parser('roll',help='roll help')
# roll_sub = parser_roll.add_subparsers(help='roll commands')

# shared_roll_parser = argparse.ArgumentParser(add_help=False)
# adadv = shared_roll_parser.add_mutually_exclusive_group()
# adadv.add_argument('-a','--adv',action='store_true')
# adadv.add_argument('-d','--dadv',action='store_true')

# roll_init = roll_sub.add_parser('initiative',aliases=['init'])

# roll_atk = roll_sub.add_parser('attack',aliases=['atk'])

# roll_spellcast = roll_sub.add_parser('spellcast',aliases=['sc'])

# roll_dmg = roll_sub.add_parser('damage',aliases=['dmg'])

# roll_save = roll_sub.add_parser('save',aliases=['save'])
# ##########################################################################

# parser.parse_args(shlex.split("dndio get -b"))