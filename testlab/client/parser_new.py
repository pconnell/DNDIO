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

class SetValueSplitter(argparse.Action):
    def __init__(self, valid_stats, valid_values, return_values=False, **kwargs):
        self.return_values = "values" if return_values else "stats"
        self.valid_stats = valid_stats
        self.valid_values = valid_values
        super().__init__(**kwargs)
    
    def __call__(self, parser, namespace, args, option_string=None):
        if len(args) % 2 != 0:
            raise ValueError("Values must be in key-value pairs.")

        it = [iter(args)] * 2

        stats = dict(zip(*it))

        for stat in stats:
            if not (
                stat in self.valid_stats and int(stats[stat]) in self.valid_values
            ):
                raise ValueError(f"{stat}, {stats[stat]}.\nValid abilities are {self.valid_stats}, with scores ranging from {self.valid_values[0]} to {self.valid_values[-1]}.")

        setattr(namespace, self.dest, eval(self.return_values))

def create_set_value_parser(parser, name, valid_stats: list[str], valid_values: list[int]):
    parser.add_argument(
        name, 
        nargs="+", 
        action=SetValueSplitter, 
        valid_stats=valid_stats, 
        valid_values=valid_values
    )

    return parser

char_set = char_sub.add_parser('set', 
                               help="Modify a value on your, another player's, or an NPC's character sheet.", 
                               aliases=['set'])
set_sub = char_set.add_subparsers()

# Set ability score
# dndio char set ability STR 17
char_set_parsers = {
    "ability": 
        (
            ["CHA", "STR", "INT", "WIS", "DEX", "CON"], 
            list(range(1, 21))
        ),
    "skill":
        (
            ["animalhandling", "arcana", "(etc.)"],
            list(range(-5, 6))
        )
}


for target in char_set_parsers:
    value_sub = set_sub.add_parser(target)
    create_set_value_parser(
        value_sub, 
        target,
        char_set_parsers[target][0],
        char_set_parsers[target][1]        
    )

##########################################################################

#examples
def parse_str(s):
    print(s)
    print(parser.parse_args(s))
    print('*'*80)



test_commands = [
    "char set ability CHA 20 WIS 14 STR 12 INT 15",
    "char get equipped",
    "char get -b equipped",
    "char set skill animalhandling 4",
    "char set skill animalhandling 4 arcana -2"
]


for s in test_commands:
    try:
        parse_str(shlex.split(s))
    except Exception as e:
        print(e)

#### NOTES ####
# - for `init`